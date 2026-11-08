"""Workspace Clip, movable launchers, and responsive side dock.
Only process-local drag payloads are accepted; dropping never runs a shell.
"""
import json,uuid,math
from PySide6.QtCore import Qt,QObject,QEvent,QMimeData,QSize,QPoint,QTimer
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import *
from foundation import icon
from drawers import INTERNAL,load_drawers,launch_entry
from running_dock import app_kind,ICONS
MIME='application/x-macaquestep-launcher-v1'
# Action aliases used by the legacy docks and the running-window task list.
ACTION={'monkey':'about','files':'files','terminal':'terminal','editor':'editor','apps':'launcher','camera':'screenshot','screenshot':'screenshot','settings':'preferences','calculator':'calculator','images':'images','windows':'window_list','notes':'notes','tasks':'tasks','media':'media','system':'system_info','paint':'paint','archive':'archives','help':'help_center','search':'search','host-apps':'host_apps','backups':'backups','controls':'system_controls','drawer-shelf':'drawer_shelf','drawers':'drawer_shelf','window-rules':'rules_panel','sounds':'sound_preferences','settings-hub':'settings_hub','sessions':'sessions_panel','shortcuts':'shortcuts_panel','unix-readiness':'readiness_panel','clock':'clock','about':'about','preferences':'preferences','launcher':'launcher','window-list':'window_list','project-status':'project_status','image':'images'}
ACTION.update({'setup': 'setup_assistant', 'software': 'software_center', 'accessibility': 'accessibility_panel', 'lock-sleep': 'lock_sleep', 'personal-backups': 'personal_recovery'})
ACTION.update({'dual-files': 'dual_files', 'disk-usage': 'disk_usage', 'system-monitor': 'system_monitor', 'checksums': 'checksum_tool', 'recent': 'recent_documents', 'activity': 'activity_center'})
ACTION_ICON={value:ICONS.get(key,key) for key,value in ACTION.items()}
ACTION_ICON.update({'paint':'paint','search':'search','clock':'clock','drawer_shelf':'drawers','about':'monkey','preferences':'settings','window_list':'windows','help_center':'help','system_info':'system','images':'image','launcher':'apps','screenshot':'camera'})
def valid_entry(value):
 if not isinstance(value,dict) or not isinstance(value.get('name'),str) or not value['name'].strip():return None
 action=value.get('action');command=value.get('command')
 if isinstance(action,str) and action in INTERNAL:entry={'name':value['name'][:80],'action':action}
 elif isinstance(command,str) and 0<len(command)<=4096:entry={'name':value['name'][:80],'command':command}
 else:return None
 if isinstance(value.get('id'),str) and 0<len(value['id'])<=100:entry['id']=value['id']
 return entry
def entries_json(settings,key,default):
 try:rows=json.loads(settings.value(key,json.dumps(default)))
 except (TypeError,ValueError):rows=default
 if not isinstance(rows,list):rows=default
 return [entry for row in rows[:100] if (entry:=valid_entry(row)) is not None]
def entry_icon(entry):return icon(ACTION_ICON.get(entry.get('action'),'apps'))
class DockEvents(QObject):
 def __init__(self,d):super().__init__(d);self.d=d;self.sources={};self.targets={};self.pressed=None
 def source(self,widget,callback):
  if widget not in self.sources:widget.installEventFilter(self);widget.destroyed.connect(lambda *_ ,w=widget:self.sources.pop(w,None))
  self.sources[widget]=callback
 def target(self,widget,callback):
  if widget not in self.targets:widget.installEventFilter(self);widget.setAcceptDrops(True);widget.destroyed.connect(lambda *_ ,w=widget:self.targets.pop(w,None))
  self.targets[widget]=callback
 def payload(self,mime):
  if not mime.hasFormat(MIME):return None
  raw=bytes(mime.data(MIME))
  if len(raw)>12000:return None
  try:value=json.loads(raw)
  except (ValueError,TypeError):return None
  if not isinstance(value,dict) or value.get('token')!=self.d._dock_token or not valid_entry(value.get('entry')):return None
  source=value.get('source')
  if not isinstance(source,dict) or source.get('type') not in ('side','clip','drawer','running','catalog'):return None
  return value
 def eventFilter(self,obj,event):
  d=self.d
  if d.exiting:return False
  kind=event.type()
  if obj in self.targets and kind in (QEvent.DragEnter,QEvent.DragMove):
   if self.payload(event.mimeData()):event.acceptProposedAction();return True
   event.ignore();return True
  if obj in self.targets and kind==QEvent.Drop:
   payload=self.payload(event.mimeData())
   if payload:
    target=self.targets[obj](event.position().toPoint());copy=bool(event.modifiers() & Qt.ControlModifier)
    if d.transfer_launcher(payload,target,copy):event.setDropAction(Qt.CopyAction if copy or target.get('type')=='running' or payload['source']['type'] in ('running','catalog') else Qt.MoveAction);event.accept();return True
   event.ignore();return True
  if obj in self.sources:
   if kind==QEvent.MouseButtonPress and event.button()==Qt.LeftButton:self.pressed=(obj,event.position().toPoint())
   elif kind==QEvent.MouseButtonDblClick and event.button()==Qt.LeftButton and d.settings.value('dock_double_click',False,type=bool):
    payload=self.sources[obj]();self.pressed=None
    if payload:
     if payload['source']['type']=='running':d.running_dock.activate_group(payload['source']['group'])
     else:launch_entry(d,payload['entry'])
    if isinstance(obj,QAbstractButton):obj.setDown(False)
    return True
   elif kind==QEvent.MouseButtonRelease:
    self.pressed=None
    if event.button()==Qt.LeftButton and d.settings.value('dock_double_click',False,type=bool):
     if isinstance(obj,QAbstractButton):obj.setDown(False)
     return True
   elif kind==QEvent.MouseMove and event.buttons() & Qt.LeftButton and self.pressed and self.pressed[0] is obj and (event.position().toPoint()-self.pressed[1]).manhattanLength()>=QApplication.startDragDistance():
    payload=self.sources[obj]()
    self.pressed=None
    if payload:
     payload['token']=d._dock_token;mime=QMimeData();mime.setData(MIME,json.dumps(payload).encode());drag=QDrag(obj);drag.setMimeData(mime);drag.setPixmap(entry_icon(payload['entry']).pixmap(40,40));d._dock_dragging=True
     if isinstance(obj,QAbstractButton):obj.setDown(False)
     try:drag.exec(Qt.CopyAction|Qt.MoveAction,Qt.MoveAction)
     finally:d._dock_dragging=False;d.refresh_docks();d.queue_running_refresh()
     return True
  return False
class DockWorkspace:
 def setup_workspace_docks(self):
  self._dock_token=uuid.uuid4().hex;self._dock_dragging=False;self._dock_defaults=[];self._dock_legacy={};self.dock_events=DockEvents(self)
  for key,b in self.dock_buttons.items():
   action=ACTION.get(key)
   if action in INTERNAL:
    entry={'id':'builtin:'+key,'name':INTERNAL[action],'action':action};self._dock_defaults.append(entry);self._dock_legacy[entry['id']]=b
    if action!='drawer_shelf':
     b.clicked.disconnect();b.clicked.connect(lambda checked=False,e=dict(entry):launch_entry(self,e))
  self.side_launchers=entries_json(self.settings,'dock_launchers_v12',self._dock_defaults)
  seen=set();defaults={entry['id']:entry for entry in self._dock_defaults}
  for entry in self.side_launchers:
   identity=entry.get('id')
   if not identity or identity in seen or (identity in defaults and defaults[identity].get('action')!=entry.get('action')):entry['id']=uuid.uuid4().hex
   seen.add(entry['id'])
  # Replace the vertical layout with a grid, retaining the existing scroll area and dock side.
  old=self.dock_scroll.takeWidget()
  if old:
   for b in self.dock_buttons.values():b.setParent(self);b.hide()
   old.deleteLater()
  panel=QWidget();panel.setObjectName('dockPanel');self.side_grid=QGridLayout(panel);self.side_grid.setContentsMargins(5,5,5,5);self.side_grid.setAlignment(Qt.AlignTop|Qt.AlignHCenter);self.dock_scroll.setWidget(panel);self.dock_events.target(panel,lambda pos:{'type':'side'});self.dock_events.target(self.dock_scroll.viewport(),lambda pos:{'type':'side'});self.dock_scroll.viewport().installEventFilter(self);self.side_widgets=[]
  self.clip=WorkspaceClip(self);self.clip.setParent(self.area.viewport());self.refresh_docks()
 def clip_entries(self,n=None):return entries_json(self.settings,'clip_launchers_'+str(self.workspace if n is None else n),[])
 def write_location(self,location,entries):
  kind=location['type']
  if kind=='side':self.side_launchers=entries;self.settings.setValue('dock_launchers_v12',json.dumps(entries))
  elif kind=='clip':self.settings.setValue('clip_launchers_'+str(location['workspace']),json.dumps(entries))
  elif kind=='drawer':
   drawers=load_drawers(self.settings);index=location['drawer']
   if not 0<=index<len(drawers):raise ValueError('Drawer no longer exists.')
   drawers[index]['entries']=entries;self.settings.setValue('wm_drawers',json.dumps(drawers))
 def location_entries(self,location):
  kind=location.get('type')
  if kind=='side':return list(self.side_launchers)
  if kind=='clip' and type(location.get('workspace'))==int and 0<=location['workspace']<4:return self.clip_entries(location['workspace'])
  if kind=='drawer' and type(location.get('drawer'))==int:
   drawers=load_drawers(self.settings);i=location['drawer']
   if 0<=i<len(drawers):return drawers[i]['entries']
  raise ValueError('Invalid launcher destination.')
 def transfer_launcher(self,payload,target,copy=False):
  if not isinstance(payload,dict) or not isinstance(target,dict):return False
  entry=valid_entry(payload.get('entry'));source=payload.get('source',{})
  if not isinstance(source,dict):return False
  if entry is None:return False
  if target.get('type')=='running':
   return self.set_pin(entry,'running',True)
  try:
   destination=self.location_entries(target);origin=None;index=source.get('index');same=all(source.get(k)==target.get(k) for k in ('type','workspace','drawer'))
   if source.get('type') in ('side','clip','drawer'):
    origin=self.location_entries(source)
    if type(index)!=int or not 0<=index<len(origin) or valid_entry(origin[index])!=entry:return False
   if len(destination)>=100 and not (same and not copy):return False
   insert=target.get('index',len(destination));insert=max(0,min(len(destination),insert)) if type(insert)==int else len(destination)
   if origin is not None and not copy:
    origin.pop(index)
    if same:
     destination=origin
     if index<insert:insert-=1
    else:self.write_location(source,origin)
   if copy or source.get('type') in ('running','catalog'):entry['id']=uuid.uuid4().hex
   else:entry.setdefault('id',uuid.uuid4().hex)
   destination.insert(insert,entry);self.write_location(target,destination);self.refresh_docks();return True
  except (ValueError,KeyError,TypeError):return False
 def refresh_docks(self):
  if not hasattr(self,'clip') or self.exiting or self._dock_dragging:return
  for b in getattr(self,'side_widgets',[]):self.side_grid.removeWidget(b);b.hide()
  self.side_widgets=[]
  active_ids={entry.get('id') for entry in self.side_launchers};builtin_ids={entry['id'] for entry in self._dock_defaults}
  for identity in list(self._dock_legacy):
   if identity not in active_ids and identity not in builtin_ids:
    button=self._dock_legacy.pop(identity);self.dock_buttons.pop('pin-'+identity,None);button.deleteLater()
  for i,entry in enumerate(self.side_launchers):
   identity=entry.get('id');b=self._dock_legacy.get(identity)
   if b is None:
    b=QPushButton();b.setObjectName('dock')
    if entry.get('action')!='drawer_shelf':b.clicked.connect(lambda checked=False,e=dict(entry):launch_entry(self,e))
    self._dock_legacy[identity]=b;self.dock_buttons['pin-'+identity]=b
   # Drawers now opens the draggable shelf; menu remains on the top bar.
   if entry.get('action')=='drawer_shelf':
    b.setMenu(None)
    if not b.property('shelf_connected'):b.clicked.connect(self.drawer_shelf);b.setProperty('shelf_connected',True)
   b.setIcon(entry_icon(entry));b.setToolTip(entry['name']+'\nDrag to another dock; Ctrl-drag copies. Right-click for launcher options.');b.setAccessibleName(entry['name']);b.setContextMenuPolicy(Qt.CustomContextMenu)
   if not b.property('launcher_context'):
    b.customContextMenuRequested.connect(lambda pos,button=b:self.side_context(button,pos));b.setProperty('launcher_context',True)
   self.dock_events.source(b,lambda index=i:{'entry':dict(self.side_launchers[index]),'source':{'type':'side','index':index}});self.dock_events.target(b,lambda pos,index=i:{'type':'side','index':index});self.side_widgets.append(b)
  self.fit_side_dock();self.clip.refresh();self.refresh_drawer_menu()
  for w in list(self.windows.values()):
   if isinstance(w.content,DrawerShelf):w.content.refresh()
   elif hasattr(w.content,'drawers') and w.content.__class__.__name__=='DrawerEditor':w.content.drawers=load_drawers(self.settings);w.content.reload()
 def side_context(self,button,pos):
  if button not in self.side_widgets:return
  i=self.side_widgets.index(button);menu=QMenu(self);self.pin_menu(menu,self.side_launchers[i]);menu.addAction('Move to this workspace Clip',lambda:self.transfer_launcher({'entry':self.side_launchers[i],'source':{'type':'side','index':i}},{'type':'clip','workspace':self.workspace}));menu.addAction('Remove launcher',lambda:self.remove_launcher({'type':'side'},i));menu.addAction('Dock preferences…',self.preferences);menu.addAction('Restore default side launchers',self.restore_side_launchers);menu.exec(button.mapToGlobal(pos))
 def remove_launcher(self,location,index):
  entries=self.location_entries(location)
  if 0<=index<len(entries):entries.pop(index);self.write_location(location,entries);self.refresh_docks()
 def restore_side_launchers(self):self.write_location({'type':'side'},[dict(e) for e in self._dock_defaults]);self.refresh_docks()
 def fit_side_dock(self):
  if not hasattr(self,'side_grid'):return
  fit=self.settings.value('dock_fit',False,type=bool);desired=max(24,min(68,int(self.settings.value('dock_size',48))));count=len(self.side_widgets);height=max(80,self.dock_scroll.viewport().height()-10);gap=4
  columns=1
  if fit:
   capacity=max(1,(height+gap)//(desired+gap));columns=max(1,math.ceil(count/capacity));rows=max(1,math.ceil(count/columns));size=desired
  else:size=desired;rows=max(1,count)
  self.effective_dock_size=size;self.side_grid.setSpacing(gap)
  for i,b in enumerate(self.side_widgets):self.side_grid.removeWidget(b);b.setFixedSize(size,size);b.setIconSize(QSize(max(16,size-14),max(16,size-14)));self.side_grid.addWidget(b,i%rows,i//rows);b.show()
  self.dock_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff if fit else Qt.ScrollBarAsNeeded);self.dock_scroll.setFixedWidth(columns*(size+gap)+10+(0 if fit else 16));self.dock_scroll.widget().setMinimumHeight(0 if fit else count*(size+gap)+10)
  if hasattr(self,'running_dock'):self.running_dock.signature=None;self.queue_running_refresh()
 def launcher_catalog(self):
  dialog=QDialog(self);dialog.setWindowTitle('Add launcher to Clip');v=QVBoxLayout(dialog);items=QListWidget();items.addItems(sorted(INTERNAL.values()));v.addWidget(items);buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);v.addWidget(buttons);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
  if dialog.exec()==QDialog.Accepted and items.currentItem():
   name=items.currentItem().text();action=next(k for k,value in INTERNAL.items() if value==name);self.transfer_launcher({'entry':{'name':name,'action':action},'source':{'type':'catalog'}},{'type':'clip','workspace':self.workspace},True)
 def drawer_shelf(self):
  if 'drawer-shelf' in self.windows:self.reopen('drawer-shelf');return
  self.window('drawer-shelf','Launcher Drawer Shelf',DrawerShelf(self),(100,80,640,450))
 def running_drag(self,group):
  keys=self.running_dock.groups().get(group,[])
  entry=self.running_dock.pinned_entries.get(group)
  if entry:return {'entry':dict(entry),'source':{'type':'running','group':group}}
  if not keys:return None
  kind=app_kind(keys[0]);action=ACTION.get(kind)
  if action not in INTERNAL:return None
  return {'entry':{'name':INTERNAL[action],'action':action},'source':{'type':'running','group':group}}
class WorkspaceClip(QFrame):
 def __init__(self,d):
  super().__init__();self.d=d;self.setObjectName('workspaceClip');v=QVBoxLayout(self);v.setContentsMargins(5,5,5,5);row=QHBoxLayout();v.addLayout(row)
  prev=QToolButton();prev.setObjectName('clipNav');prev.setText('◀');prev.setToolTip('Previous workspace');prev.clicked.connect(lambda:d.switch_workspace((d.workspace-1)%4));row.addWidget(prev)
  self.anchor=QToolButton();self.anchor.setObjectName('runningTile');self.anchor.setIcon(icon('clip'));self.anchor.setIconSize(QSize(30,30));self.anchor.setFixedSize(44,44);self.anchor.clicked.connect(self.toggle);self.anchor.setToolTip('Workspace Clip — click to collapse or expand; drop launchers here');row.addWidget(self.anchor);self.label=QLabel();self.label.setMaximumWidth(150);row.addWidget(self.label)
  next_button=QToolButton();next_button.setObjectName('clipNav');next_button.setText('▶');next_button.setToolTip('Next workspace');next_button.clicked.connect(lambda:d.switch_workspace((d.workspace+1)%4));row.addWidget(next_button);self.grid_widget=QWidget();self.grid=QGridLayout(self.grid_widget);self.grid.setContentsMargins(0,0,0,0);self.grid.setSpacing(4);v.addWidget(self.grid_widget);self.buttons=[];self.setContextMenuPolicy(Qt.CustomContextMenu);self.customContextMenuRequested.connect(self.menu);d.dock_events.target(self,lambda pos:{'type':'clip','workspace':d.workspace});d.dock_events.target(self.anchor,lambda pos:{'type':'clip','workspace':d.workspace})
 def toggle(self):self.d.settings.setValue('clip_collapsed_'+str(self.d.workspace),not self.d.settings.value('clip_collapsed_'+str(self.d.workspace),False,type=bool));self.refresh()
 def refresh(self):
  if self.d._dock_dragging:return
  for b in self.buttons:self.grid.removeWidget(b);b.deleteLater()
  self.buttons=[];d=self.d;entries=d.clip_entries();self.label.setText(str(d.workspace+1)+' · '+d.workspace_name(d.workspace));self.label.setToolTip(d.workspace_name(d.workspace));size=max(24,min(68,getattr(d,'effective_dock_size',44)));available=max(80,d.work_rect().height()-90);width=max(100,d.area.viewport().width()-30)
  while size>20 and max(1,available//(size+4))*max(1,width//(size+4))<len(entries):size-=1
  rows=max(1,available//(size+4));cols=min(max(1,width//(size+4)),max(3,math.ceil(len(entries)/rows)))
  for i,entry in enumerate(entries):
   b=QToolButton();b.setObjectName('runningTile');b.setToolButtonStyle(Qt.ToolButtonIconOnly);b.setIcon(entry_icon(entry));b.setIconSize(QSize(size-12,size-12));b.setFixedSize(size,size);b.setToolTip(entry['name']);b.setAccessibleName(entry['name']);b.clicked.connect(lambda checked=False,e=entry:launch_entry(d,e));b.setContextMenuPolicy(Qt.CustomContextMenu);b.customContextMenuRequested.connect(lambda pos,index=i,button=b:self.entry_menu(button,index,pos));self.grid.addWidget(b,i//cols,i%cols);self.buttons.append(b);d.dock_events.source(b,lambda index=i:{'entry':d.clip_entries()[index],'source':{'type':'clip','workspace':d.workspace,'index':index}});d.dock_events.target(b,lambda pos,index=i:{'type':'clip','workspace':d.workspace,'index':index})
  self.grid_widget.setVisible(bool(entries) and not d.settings.value('clip_collapsed_'+str(d.workspace),False,type=bool));self.adjustSize();self.move(8,8);self.setVisible(d.settings.value('clip_visible',True,type=bool));self.raise_()
 def entry_menu(self,button,index,pos):
  menu=QMenu(self);self.d.pin_menu(menu,self.d.clip_entries()[index]);menu.addAction('Remove from Clip',lambda:self.d.remove_launcher({'type':'clip','workspace':self.d.workspace},index));menu.addAction('Copy to side dock',lambda:self.d.transfer_launcher({'entry':self.d.clip_entries()[index],'source':{'type':'clip','workspace':self.d.workspace,'index':index}},{'type':'side'},True));spaces=menu.addMenu('Move to workspace Clip')
  for n in range(4):spaces.addAction(self.d.workspace_name(n),lambda checked=False,target=n:self.d.transfer_launcher({'entry':self.d.clip_entries()[index],'source':{'type':'clip','workspace':self.d.workspace,'index':index}},{'type':'clip','workspace':target}))
  menu.exec(button.mapToGlobal(pos))
 def menu(self,pos):
  menu=QMenu(self);menu.addAction('Add built-in launcher…',self.d.launcher_catalog);menu.addAction('Rename workspace…',lambda:self.d.rename_workspace(self.d.workspace));menu.addAction('Collapse / expand',self.toggle);menu.addAction('Dock preferences…',self.d.preferences);menu.exec(self.mapToGlobal(pos))
class DrawerShelf(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;v=QVBoxLayout(self);self.choose=QComboBox();v.addWidget(self.choose);self.body=QWidget();self.body.setObjectName('drawerShelfBody');self.body.setAttribute(Qt.WA_StyledBackground,True);self.grid=QGridLayout(self.body);self.grid.setAlignment(Qt.AlignTop|Qt.AlignLeft);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(self.body);v.addWidget(scroll,1);note=QLabel('Drag icons between this shelf, the side dock, and the workspace Clip. Ctrl-drag copies. Dropping onto the running-app dock pins the app without launching it.');note.setWordWrap(True);v.addWidget(note);edit=QPushButton('Customize drawers…');edit.clicked.connect(d.open_drawers);v.addWidget(edit);self.buttons=[];self.choose.currentIndexChanged.connect(self.refresh);d.dock_events.target(self.body,lambda pos:{'type':'drawer','drawer':self.choose.currentIndex()});d.dock_events.target(scroll.viewport(),lambda pos:{'type':'drawer','drawer':self.choose.currentIndex()});self.refresh()
 def refresh(self):
  if self.d._dock_dragging:return
  index=max(0,self.choose.currentIndex());drawers=load_drawers(self.d.settings);self.choose.blockSignals(True);self.choose.clear();self.choose.addItems([row['name'] for row in drawers]);self.choose.setCurrentIndex(min(index,len(drawers)-1));self.choose.blockSignals(False)
  for b in self.buttons:self.grid.removeWidget(b);b.deleteLater()
  self.buttons=[];index=self.choose.currentIndex()
  if index<0:return
  for i,entry in enumerate(drawers[index]['entries']):
   b=QToolButton();b.setObjectName('runningTile');b.setToolButtonStyle(Qt.ToolButtonIconOnly);b.setIcon(entry_icon(entry));size=getattr(self.d,'effective_dock_size',48);b.setIconSize(QSize(max(16,size-14),max(16,size-14)));b.setFixedSize(size,size);b.setText(entry['name'][:15].replace('&','&&'));b.setToolTip(entry['name']);b.setContextMenuPolicy(Qt.CustomContextMenu);b.customContextMenuRequested.connect(lambda pos,button=b,e=dict(entry):self.pin_context(button,e,pos));b.clicked.connect(lambda checked=False,e=entry:launch_entry(self.d,e));self.grid.addWidget(b,i//4,i%4);self.buttons.append(b);self.d.dock_events.source(b,lambda e=entry,n=i:{'entry':e,'source':{'type':'drawer','drawer':self.choose.currentIndex(),'index':n}});self.d.dock_events.target(b,lambda pos,n=i:{'type':'drawer','drawer':self.choose.currentIndex(),'index':n})

 def pin_context(self,button,entry,pos):
  menu=QMenu(self);self.d.pin_menu(menu,entry);menu.exec(button.mapToGlobal(pos))
