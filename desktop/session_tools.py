"""Bounded, data-only desktop layouts. Never saves document bodies or shell commands."""
import json,math
from PySide6.QtCore import Qt,QRect
from PySide6.QtWidgets import *
from running_dock import app_kind
SAFE_OPEN={'files':'files','about':'about','calculator':'calculator','clock':'clock_app','notes':'notes','tasks':'tasks','help':'help_center','search':'search_files','settings-hub':'settings_hub','sounds':'sound_preferences'}
SAFE_OPEN.update({'setup': 'setup_assistant', 'software': 'software_center', 'accessibility': 'accessibility_panel', 'lock-sleep': 'lock_sleep', 'personal-backups': 'personal_recovery'})
SAFE_OPEN.update({'dual-files': 'dual_files', 'disk-usage': 'disk_usage', 'system-monitor': 'system_monitor', 'checksums': 'checksum_tool', 'recent': 'recent_documents', 'activity': 'activity_center'})
def clean_layout(value):
 if not isinstance(value,dict) or value.get('format')!=1:raise ValueError('Unsupported desktop layout.')
 entries=value.get('windows');names=value.get('names');workspace=value.get('workspace')
 if not isinstance(entries,list) or len(entries)>100 or not isinstance(names,list) or len(names)!=4 or any(not isinstance(n,str) or not n.strip() or len(n)>24 for n in names) or type(workspace)!=int or not 0<=workspace<4:raise ValueError('Invalid workspace layout.')
 result=[]
 for row in entries:
  if not isinstance(row,dict):raise ValueError('Invalid window entry.')
  key=row.get('key');kind=row.get('kind');rect=row.get('rect');space=row.get('workspace')
  if not isinstance(key,str) or len(key)>200 or not isinstance(kind,str) or kind!=app_kind(key) or not isinstance(rect,list) or len(rect)!=4 or any(type(n)!=int or abs(n)>32768 for n in rect) or rect[2]<1 or rect[3]<1 or type(space)!=int or not 0<=space<4:raise ValueError('Invalid window geometry.')
  result.append({**{k:row.get(k) is True for k in ('sticky','above','shaded','minimized','maximized','hidden')},'key':key,'kind':kind,'rect':rect,'workspace':space})
 return {'format':1,'names':names,'workspace':workspace,'windows':result}
def load_profiles(settings):
 try:
  values=json.loads(settings.value('session_profiles','{}'))
  if not isinstance(values,dict):return {}
  result={}
  for name,value in list(values.items())[:20]:
   if isinstance(name,str) and 0<len(name)<=40:
    try:result[name]=clean_layout(value)
    except ValueError:pass
  return result
 except (ValueError,TypeError):return {}
class SessionTools:
 def capture_layout(self):
  rows=[]
  for key,w in self.windows.items():
   if key=='sessions':continue
   rect=w.property('before_minimize') if w.isMinimized() else w.property('normal_rect') if w.isMaximized() else w.geometry()
   if not isinstance(rect,QRect) or not rect.isValid():rect=w.geometry()
   if w.property('shaded') and hasattr(w,'_shade_size'):rect=QRect(w.pos(),w._shade_size)
   rows.append({'key':key,'kind':app_kind(key),'rect':[rect.x(),rect.y(),rect.width(),rect.height()],'workspace':w.property('workspace') or 0,'sticky':bool(w.property('sticky')),'above':bool(w.property('keep_above')),'hidden':bool(w.property('app_hidden')),'shaded':bool(w.property('shaded')),'minimized':w.isMinimized(),'maximized':w.isMaximized() or (w.isMinimized() and bool(w.property('restore_maximized')))})
  return clean_layout({'format':1,'names':self.workspace_names(),'workspace':self.workspace,'windows':rows[:100]})
 def apply_layout(self,value,open_missing=False,remember=True):
  value=clean_layout(value)
  if remember:self._layout_undo=self.capture_layout()
  self._desktop_hidden=[];used=set();applied=0;skipped=0
  for row in value['windows']:
   key=row['key']
   if key not in self.windows or key in used:key=next((k for k in self.windows if app_kind(k)==row['kind'] and k not in used),None)
   if key is None and open_missing and row['kind'] in SAFE_OPEN:
    getattr(self,SAFE_OPEN[row['kind']])();key=next((k for k in self.windows if app_kind(k)==row['kind'] and k not in used),None)
   if key is None:skipped+=1;continue
   used.add(key);w=self.windows[key];self.set_shaded(key,False);w.showNormal();w.setProperty('restore_maximized',False);w.setProperty('workspace',row['workspace']);w.setProperty('app_hidden',row['hidden']);w.setProperty('sticky',row['sticky']);w.setProperty('keep_above',row['above']);w.setGeometry(QRect(*row['rect']));self.ensure_visible(w)
   if row['maximized']:w.setProperty('normal_rect',w.geometry());w.showMaximized()
   if row['shaded']:self.set_shaded(key,True)
   if row['minimized']:self.minimize_running(key)
   applied+=1
  self.settings.setValue('wm_workspace_names',json.dumps(value['names']));self.refresh_workspace_names();self.switch_workspace(value['workspace']);self.enforce_stacking();self.queue_running_refresh()
  return applied,skipped
 def undo_layout(self):
  value=getattr(self,'_layout_undo',None)
  if value is not None:self.apply_layout(value,remember=False);self._layout_undo=None
 def arrange_windows(self,mode):
  windows=[(k,w) for k,w in self.windows.items() if w.isVisible() and not w.isMinimized() and k!='sessions']
  if not windows:return
  self._layout_undo=self.capture_layout();r=self.work_rect();count=len(windows);cols=math.ceil(math.sqrt(count));rows=math.ceil(count/cols)
  for i,(key,w) in enumerate(windows):
   self.set_shaded(key,False);w.showNormal()
   if mode=='tile':
    x=i%cols*r.width()//cols;y=i//cols*r.height()//rows;right=(i%cols+1)*r.width()//cols;bottom=(i//cols+1)*r.height()//rows;w.setGeometry(x,y,right-x,bottom-y)
   else:
    offset=(i%8)*28;w.setGeometry(offset,offset,max(300,r.width()*2//3),max(160,r.height()*2//3))
   self.ensure_visible(w)
  self.enforce_stacking()
 def show_desktop(self):
  hidden=getattr(self,'_desktop_hidden',[])
  if hidden:
   workspace=self.workspace
   for key in hidden:
    if key in self.windows:self.activate_running(key,False)
   self._desktop_hidden=[];self.switch_workspace(workspace);return
  self._desktop_hidden=[key for key,w in self.windows.items() if w.isVisible() and not w.isMinimized()]
  for key in self._desktop_hidden:self.minimize_running(key)
 def sessions_panel(self):
  if 'sessions' in self.windows:self.reopen('sessions');return
  self.window('sessions','Desktop Sessions',SessionsPanel(self),(110,60,710,560))
class SessionsPanel(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;v=QVBoxLayout(self);intro=QLabel('Save window positions, workspace names, and window states. Loading leaves other open windows and unsaved documents in place. Document contents and terminal sessions are not saved.');intro.setWordWrap(True);v.addWidget(intro);self.items=QListWidget();v.addWidget(self.items,1)
  self.open_missing=QCheckBox('Open missing supported tools (Files, Notes, Tasks, Calculator, Clock, Help, Search, Settings, Sounds, About)')
  # Keep the long label readable in compact windows.
  self.open_missing.setText('Open missing supported built-in tools');self.open_missing.setToolTip('Never launches commands, terminals, documents, media, or external applications.');v.addWidget(self.open_missing)
  row=QHBoxLayout()
  for label,callback in [('Save current…',self.save),('Load selected',self.load),('Delete',self.delete),('Undo layout',d.undo_layout)]:b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
  v.addLayout(row);row=QHBoxLayout();row.addWidget(QLabel('On startup'));self.startup=QComboBox();self.startup.currentIndexChanged.connect(self.startup_changed);row.addWidget(self.startup,1);v.addLayout(row);self.status=QLabel('Startup restoration arranges core windows and opens only the supported tools listed in Help.');self.status.setWordWrap(True);v.addWidget(self.status);self.refresh()
 def refresh(self):
  chosen=self.items.currentItem().text() if self.items.currentItem() else '';self.items.clear();profiles=load_profiles(self.d.settings);self.items.addItems(sorted(profiles));matches=self.items.findItems(chosen,Qt.MatchExactly)
  if matches:self.items.setCurrentItem(matches[0])
  elif self.items.count():self.items.setCurrentRow(0)
  self.startup.blockSignals(True);self.startup.clear();self.startup.addItem('Default startup','');
  for name in sorted(profiles):self.startup.addItem(name,name)
  self.startup.setCurrentIndex(max(0,self.startup.findData(self.d.settings.value('session_startup',''))));self.startup.blockSignals(False)
 def startup_changed(self):self.d.settings.setValue('session_startup',self.startup.currentData() or '')
 def save(self):
  name,ok=QInputDialog.getText(self,'Save desktop session','Session name (40 characters maximum)')
  if not ok or not name.strip():return
  name=name.strip()[:40];profiles=load_profiles(self.d.settings)
  if name in profiles and QMessageBox.question(self,'Replace session','Replace the saved session '+name+'?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
  if name not in profiles and len(profiles)>=20:self.status.setText('Maximum 20 sessions. Delete one first.');return
  profiles[name]=self.d.capture_layout();self.d.settings.setValue('session_profiles',json.dumps(profiles));self.refresh();self.status.setText('Saved '+name+'. Documents and commands are not included.')
 def load(self):
  item=self.items.currentItem()
  if item:
   value=load_profiles(self.d.settings).get(item.text())
   if value is not None:
    applied,skipped=self.d.apply_layout(value,self.open_missing.isChecked());self.status.setText(f'Arranged {applied} windows; {skipped} unavailable. Other windows remain open. Undo layout restores the previous arrangement.')
 def delete(self):
  item=self.items.currentItem()
  if not item:return
  if QMessageBox.question(self,'Delete session','Delete saved layout '+item.text()+'?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
  profiles=load_profiles(self.d.settings);profiles.pop(item.text(),None);self.d.settings.setValue('session_profiles',json.dumps(profiles))
  if self.d.settings.value('session_startup','')==item.text():self.d.settings.setValue('session_startup','')
  self.refresh()
