import json,shlex,shutil
from PySide6.QtCore import Qt,QProcess
from PySide6.QtWidgets import *
INTERNAL={'editor':'Text Editor','calculator':'Calculator','clock':'Clock & Timer','notes':'Notes','tasks':'Tasks','paint':'Paint','search':'File Search','settings_hub':'Settings','system_controls':'System Controls','backups':'Backups','system_info':'System Report','sound_preferences':'Sound Effects','rules_panel':'Window Rules','sessions_panel':'Desktop Sessions','shortcuts_panel':'Keyboard Shortcuts','readiness_panel':'Unix Readiness Inventory'}
INTERNAL.update({'overview':'Workspace Overview','command_palette':'Command Palette','files': 'File Viewer', 'terminal': 'Terminal', 'about': 'About', 'launcher': 'Applications', 'screenshot': 'Screenshot', 'preferences': 'Preferences', 'images': 'Image Viewer', 'window_list': 'Open Windows', 'media': 'Media Player', 'archives': 'Archive Viewer', 'help_center': 'Help', 'host_apps': 'Installed Apps', 'project_status': 'Project Status', 'drawer_shelf': 'Drawer Shelf'})
INTERNAL.update({'setup_assistant': 'Setup Assistant', 'software_center': 'Software Center', 'accessibility_panel': 'Accessibility', 'lock_sleep': 'Lock & Sleep', 'personal_recovery': 'Personal Backup & Recovery'})
INTERNAL.update({'dual_files': 'Two-Pane Files', 'disk_usage': 'Disk Usage', 'system_monitor': 'System Monitor', 'checksum_tool': 'File Checksums', 'recent_documents': 'Recent Documents', 'activity_center': 'Activity Center'})
DEFAULT=[{'name':'Utilities','entries':[{'name':'Text Editor','action':'editor'},{'name':'Calculator','action':'calculator'},{'name':'Clock & Timer','action':'clock'}]},{'name':'System','entries':[{'name':'Settings','action':'settings_hub'},{'name':'Sound Effects','action':'sound_preferences'},{'name':'Backups','action':'backups'},{'name':'Window Rules','action':'rules_panel'}]}]
def load_drawers(settings):
 try:drawers=json.loads(settings.value('wm_drawers',json.dumps(DEFAULT)))
 except (TypeError,ValueError):drawers=DEFAULT
 if not isinstance(drawers,list):drawers=DEFAULT
 valid=[]
 for drawer in drawers[:20]:
  if not isinstance(drawer,dict) or not isinstance(drawer.get('name'),str) or not isinstance(drawer.get('entries'),list):continue
  entries=[]
  for entry in drawer['entries'][:100]:
   if isinstance(entry,dict) and isinstance(entry.get('name'),str) and (isinstance(entry.get('action'),str) and entry.get('action') in INTERNAL or isinstance(entry.get('command'),str)):entries.append(entry)
  valid.append({'name':drawer['name'][:40],'entries':entries})
 return valid
class DrawerEditor(QWidget):
 def __init__(self,desktop):
  super().__init__();self.desktop=desktop;self.drawers=load_drawers(desktop.settings);v=QVBoxLayout(self);row=QHBoxLayout();self.drawer=QComboBox();row.addWidget(self.drawer,1)
  for name,fn in [('New drawer',self.new),('Rename',self.rename),('Remove drawer',self.remove_drawer)]:button=QPushButton(name);button.clicked.connect(fn);row.addWidget(button)
  v.addLayout(row);self.items=QListWidget();v.addWidget(self.items,1);row=QHBoxLayout()
  for name,fn in [('Add built-in',self.add_internal),('Add command',self.add_command),('Move up',lambda:self.move(-1)),('Move down',lambda:self.move(1)),('Remove item',self.remove_item)]:button=QPushButton(name);button.clicked.connect(fn);row.addWidget(button)
  v.addLayout(row);note=QLabel('Drawers launch built-in tools or an explicit command. External application windows open on the host desktop. Commands are split into arguments and never passed to a shell.');note.setWordWrap(True);v.addWidget(note);self.drawer.currentIndexChanged.connect(self.refresh);self.reload()
 def reload(self):
  old=self.drawer.currentIndex();self.drawer.blockSignals(True);self.drawer.clear();self.drawer.addItems([d['name'] for d in self.drawers]);self.drawer.setCurrentIndex(max(0,min(old,len(self.drawers)-1)));self.drawer.blockSignals(False);self.refresh()
 def current(self):
  i=self.drawer.currentIndex();return self.drawers[i] if 0<=i<len(self.drawers) else None
 def refresh(self):
  self.items.clear();drawer=self.current()
  if drawer:
   for entry in drawer['entries']:self.items.addItem(entry['name']+(' — host command' if 'command' in entry else ''))
 def save(self):
  self.desktop.settings.setValue('wm_drawers',json.dumps(self.drawers))
  if hasattr(self.desktop,'clip'):self.desktop.refresh_docks()
  else:self.desktop.refresh_drawer_menu()
 def new(self):
  name,ok=QInputDialog.getText(self,'New drawer','Drawer name')
  if ok and name.strip():self.drawers.append({'name':name.strip()[:40],'entries':[]});self.save();self.reload();self.drawer.setCurrentIndex(len(self.drawers)-1)
 def rename(self):
  drawer=self.current()
  if not drawer:return
  name,ok=QInputDialog.getText(self,'Rename drawer','Name',text=drawer['name'])
  if ok and name.strip():drawer['name']=name.strip()[:40];self.save();self.reload()
 def remove_drawer(self):
  if not self.current():return
  if QMessageBox.question(self,'Remove drawer','Remove this drawer and its launcher entries?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.drawers.pop(self.drawer.currentIndex());self.save();self.reload()
 def add_internal(self):
  drawer=self.current()
  if drawer is None:return
  title,ok=QInputDialog.getItem(self,'Add built-in tool','Tool',list(INTERNAL.values()),editable=False)
  if ok:action=next(k for k,v in INTERNAL.items() if v==title);drawer['entries'].append({'name':title,'action':action});self.save();self.refresh()
 def add_command(self):
  drawer=self.current()
  if drawer is None:return
  dialog=QDialog(self);dialog.setWindowTitle('Add host command');form=QFormLayout(dialog);name=QLineEdit();command=QLineEdit();command.setPlaceholderText('program "argument with spaces"');form.addRow('Label',name);form.addRow('Command',command);buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
  if dialog.exec()==QDialog.Accepted and name.text().strip() and command.text().strip():
   try:
    args=shlex.split(command.text())
    if not args:raise ValueError('Enter a program.')
   except ValueError as e:QMessageBox.warning(self,'Command',str(e));return
   drawer['entries'].append({'name':name.text().strip(),'command':command.text()});self.save();self.refresh()
 def move(self,delta):
  drawer=self.current();i=self.items.currentRow();j=i+delta
  if drawer and 0<=i<len(drawer['entries']) and 0<=j<len(drawer['entries']):drawer['entries'][i],drawer['entries'][j]=drawer['entries'][j],drawer['entries'][i];self.save();self.refresh();self.items.setCurrentRow(j)
 def remove_item(self):
  drawer=self.current();i=self.items.currentRow()
  if drawer and 0<=i<len(drawer['entries']):drawer['entries'].pop(i);self.save();self.refresh()
def launch_entry(desktop,entry):
 action=entry.get('action')
 if isinstance(action,str) and action in INTERNAL:
  if hasattr(desktop,'unhide_entry') and desktop.unhide_entry(entry):return
  method={'clock':'clock_app','paint':'paint_app','search':'search_files'}.get(action,action);callback=getattr(desktop,method,None)
  if callable(callback):callback()
  return
 try:
  args=shlex.split(entry.get('command',''))
  if not args:return
  program=shutil.which(args[0])
  if not program:raise ValueError('Program was not found: '+args[0])
  result=QProcess.startDetached(program,args[1:])
  if not result[0]:raise OSError('Application could not be launched.')
 except (ValueError,OSError) as e:QMessageBox.warning(desktop,'Launcher',str(e))
