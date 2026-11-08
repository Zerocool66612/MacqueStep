"""Persistent app pins merged with the live internal-window task dock."""
import json
def json_signature(value):return json.dumps(value,sort_keys=True)
from PySide6.QtCore import Qt,QSize,QRect,QEvent
from PySide6.QtWidgets import *
from foundation import icon
from PySide6.QtGui import QPainter,QColor,QFont

APP_NAMES={'files':'File Viewer','terminal':'Terminal','editor':'Text Editor','image':'Image Viewer','media':'Media Player','notes':'Notes','tasks':'Tasks','paint':'Paint','archive':'Archive Viewer','calculator':'Calculator','clock':'Clock & Timer','system':'System Information','preferences':'Preferences','launcher':'Applications','window-list':'Open Windows','help':'Help','about':'About','search':'File Search','host-apps':'Installed Apps','controls':'System Controls','backups':'Backups','project-status':'Project Status','sounds':'Sound Effects','settings-hub':'Settings','drawers':'Drawers','window-rules':'Window Rules','sessions':'Desktop Sessions','shortcuts':'Keyboard Shortcuts','unix-readiness':'Unix Readiness','drawer-shelf':'Drawer Shelf'}
ICONS={'files':'files','terminal':'terminal','editor':'editor','image':'image','media':'media','notes':'notes','tasks':'tasks','paint':'paint','archive':'archive','calculator':'calculator','clock':'clock','system':'system','preferences':'settings','launcher':'apps','window-list':'windows','help':'help','about':'monkey','search':'search','host-apps':'apps','controls':'settings','backups':'backups','project-status':'system','sounds':'sound','settings-hub':'settings','drawers':'files','window-rules':'settings','sessions':'windows','shortcuts':'settings','unix-readiness':'system','drawer-shelf':'drawers'}
APP_NAMES.update({'setup': 'Setup Assistant', 'software': 'Software Center', 'accessibility': 'Accessibility', 'lock-sleep': 'Lock & Sleep', 'personal-backups': 'Personal Backup & Recovery'})
ICONS.update({'setup': 'settings', 'software': 'settings', 'accessibility': 'settings', 'lock-sleep': 'settings', 'personal-backups': 'settings'})
APP_NAMES.update({'dual-files': 'Two-Pane Files', 'disk-usage': 'Disk Usage', 'system-monitor': 'System Monitor', 'checksums': 'File Checksums', 'recent': 'Recent Documents', 'activity': 'Activity Center'})
ICONS.update({'dual-files': 'files', 'disk-usage': 'system', 'system-monitor': 'system', 'checksums': 'files', 'recent': 'files', 'activity': 'files'})
def app_kind(key):
 if key.startswith('editor-'):return 'editor'
 if key.startswith('image-'):return 'image'
 return key
class AppTile(QToolButton):
 def paintEvent(self,event):
  super().paintEvent(event);count=int(self.property('windowCount') or 1)
  if count>1 or self.property('pinnedApp'):
   p=QPainter(self);
   if self.property('pinnedApp'):p.setPen(Qt.NoPen);p.setBrush(QColor('#d6bd72'));p.drawRect(3,3,5,5)
   if count<=1:return
   p.setRenderHint(QPainter.Antialiasing);p.setPen(Qt.NoPen);p.setBrush(QColor('#21b9ad'));p.drawEllipse(QRect(self.width()-19,2,17,17));p.setPen(QColor('#07302e'));p.setFont(QFont('Sans Serif',8,QFont.Bold));p.drawText(QRect(self.width()-19,2,17,17),Qt.AlignCenter,str(count) if count<100 else '+')
class RunningDock(QFrame):
 def __init__(self,desktop):
  super().__init__();self.desktop=desktop;self.setObjectName('runningDock');self.buttons={};self.signature=None
  self.setAttribute(Qt.WA_StyledBackground,False);row=QHBoxLayout(self);row.setContentsMargins(0,0,0,0)
  self.scroll=QScrollArea();self.scroll.setObjectName('runningScroll');self.scroll.setWidgetResizable(True);self.scroll.setFrameShape(QFrame.NoFrame);self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.panel=QWidget();self.panel.setObjectName('runningPanel');self.tiles=QHBoxLayout(self.panel);self.tiles.setContentsMargins(0,0,0,0);self.tiles.setSpacing(8);self.tiles.addStretch();self.scroll.setWidget(self.panel);self.scroll.viewport().setAutoFillBackground(False);self.panel.setAutoFillBackground(False);self.scroll.viewport().installEventFilter(self);row.addWidget(self.scroll)
  self.setContextMenuPolicy(Qt.CustomContextMenu);self.customContextMenuRequested.connect(lambda pos:self.options())
 def tile_size(self):
  d=self.desktop
  return getattr(d,'effective_dock_size',d.dock_buttons['files'].width()) if d.settings.value('running_follow_side',True,type=bool) else max(38,min(76,int(d.settings.value('running_icon_size',36))+20))
 def eventFilter(self,obj,event):
  if event.type()==QEvent.Wheel and obj is self.scroll.viewport():self.wheelEvent(event);return True
  return super().eventFilter(obj,event)
 def wheelEvent(self,event):
  bar=self.scroll.horizontalScrollBar();bar.setValue(bar.value()-event.angleDelta().y());event.accept()
 def groups(self):
  d=self.desktop;grouped=d.settings.value('running_group',True,type=bool);current_only=d.settings.value('running_current_only',False,type=bool);groups={}
  for key,w in d.windows.items():
   if current_only and (w.property('workspace') or 0)!=d.workspace and not w.property('sticky'):continue
   group=app_kind(key) if grouped else key;groups.setdefault(group,[]).append(key)
  self.pinned_entries={}
  pins=d.bottom_pins() if hasattr(d,'bottom_pins') else []
  if not pins:return groups
  from pinning import pin_group
  from dock_workspace import ACTION
  result={};consumed=set()
  for entry in pins:
   group=pin_group(entry);self.pinned_entries[group]=entry;keys=[key for key in d.windows if entry.get('action') and ACTION.get(app_kind(key))==entry.get('action')];result[group]=keys;consumed.update(keys)
  for group,keys in groups.items():
   remaining=[key for key in keys if key not in consumed]
   if remaining:result[group]=remaining
  return result
 def sync(self):
  d=self.desktop
  if getattr(d,'_dock_dragging',False):return
  if hasattr(d,'dock_events'):
   d.dock_events.target(self.panel,lambda pos:{'type':'running'});d.dock_events.target(self.scroll.viewport(),lambda pos:{'type':'running'})
  self.setVisible(d.settings.value('running_visible',True,type=bool));groups=self.groups();active=d.area.activeSubWindow();size=self.tile_size()
  signature=(size,json_signature(self.pinned_entries),tuple((group,tuple((key,d.windows[key].windowTitle(),d.windows[key].isMinimized(),d.windows[key].property('workspace'),d.windows[key].property('sticky'),d.windows[key].property('shaded'),d.windows[key].property('keep_above'),d.windows[key].property('app_hidden'),active is d.windows[key]) for key in keys)) for group,keys in groups.items()))
  if signature==self.signature:return
  self.signature=signature
  # Retain buttons and keyboard focus while titles/state update.
  for group in list(self.buttons):
   if group not in groups:b=self.buttons.pop(group);self.tiles.removeWidget(b);b.deleteLater()
  for group,keys in groups.items():
   if group not in self.buttons:
    b=AppTile();b.setObjectName('runningTile');b.setToolButtonStyle(Qt.ToolButtonIconOnly);b.setContextMenuPolicy(Qt.CustomContextMenu);b.clicked.connect(lambda checked=False,g=group:self.activate_group(g));b.customContextMenuRequested.connect(lambda pos,g=group:self.context(g,pos));self.tiles.insertWidget(self.tiles.count()-1,b);self.buttons[group]=b
   b=self.buttons[group];self.tiles.insertWidget(list(groups).index(group),b)
   if hasattr(d,'dock_events'):d.dock_events.source(b,lambda g=group:d.running_drag(g));d.dock_events.target(b,lambda pos:{'type':'running'})
   entry=self.pinned_entries.get(group);kind=app_kind(keys[0]) if keys else None
   if entry:
    from dock_workspace import entry_icon
    b.setIcon(entry_icon(entry))
   else:b.setIcon(icon(ICONS.get(kind,'apps')))
   b.setIconSize(QSize(max(16,size-14),max(16,size-14)));b.setFixedSize(size,size);is_active=any(d.windows[key] is active and not d.windows[key].isMinimized() and ((d.windows[key].property('workspace') or 0)==d.workspace or d.windows[key].property('sticky')) for key in keys);minimized=bool(keys) and all(d.windows[key].isMinimized() for key in keys)
   label=entry['name'] if entry else APP_NAMES.get(kind,'Window')
   if len(keys)>1:label+=f' ({len(keys)})'
   if keys and all(d.windows[key].property('app_hidden') for key in keys):label+=' — hidden'
   if minimized:label='▁ '+label
   b.setText(label);b.setAccessibleName(label);b.setProperty('windowCount',len(keys));b.setProperty('pinnedApp',bool(entry));b.setProperty('activeApp',is_active);b.setProperty('minimizedApp',minimized);b.style().unpolish(b);b.style().polish(b)
   b.setToolTip(('Pinned launcher — '+('running' if keys else 'not running')+'\n' if entry else '')+'\n'.join(f'Workspace {(d.windows[key].property("workspace") or 0)+1}: {d.windows[key].windowTitle()}' + (' — minimized' if d.windows[key].isMinimized() else '')+(' — all workspaces' if d.windows[key].property('sticky') else '')+(' — shaded' if d.windows[key].property('shaded') else '')+(' — keep above' if d.windows[key].property('keep_above') else '') for key in keys))
  self.panel.setMinimumWidth(max(1,len(groups))*(size+8)-8);self.panel.setMinimumHeight(size);self.setFixedHeight(size);self.desktop.position_running_dock()
 def activate_group(self,group):
  keys=self.groups().get(group,[])
  if not keys:
   entry=self.pinned_entries.get(group)
   if entry:
    from drawers import launch_entry
    launch_entry(self.desktop,entry)
   return
  if len(keys)>1:
   menu=QMenu(self)
   for key in keys:
    w=self.desktop.windows[key];menu.addAction(f'[{(w.property("workspace") or 0)+1}] '+w.windowTitle(),lambda checked=False,k=key:self.desktop.activate_running(k))
   menu.exec(self.buttons[group].mapToGlobal(self.buttons[group].rect().topLeft()));return
  self.desktop.activate_running(keys[0])
 def window_actions(self,menu,key):
  d=self.desktop
  if key not in d.windows:return
  w=d.windows[key];menu.addAction('Restore / Activate',lambda:d.activate_running(key,False));menu.addAction('Minimize',lambda:d.minimize_running(key));menu.addAction('Maximize / Restore',lambda:d.maximize_running(key));spaces=menu.addMenu('Move to workspace')
  for i in range(4):spaces.addAction(d.workspace_name(i),lambda checked=False,n=i:d.move_running(key,n))
  snap=menu.addMenu('Snap window')
  for position in ['Left','Right','Top','Bottom','Top left','Top right','Bottom left','Bottom right','Restore geometry']:snap.addAction(position,lambda checked=False,p=position:d.snap_window(key,p))
  d.wm_actions(menu,key);menu.addSeparator();menu.addAction('Close window',w.close)
 def context(self,group,pos):
  menu=self.context_menu(group)
  if menu is not None:menu.exec(self.buttons[group].mapToGlobal(pos))
 def context_menu(self,group):
  keys=self.groups().get(group,[]);entry=self.pinned_entries.get(group)
  if not keys and entry is None:return None
  menu=QMenu(self)
  if entry is None and keys:entry=self.desktop.entry_for_window(keys[0])
  if entry:
   from drawers import launch_entry
   menu.addAction('Launch application',lambda e=dict(entry):launch_entry(self.desktop,e))
   if len(keys)!=1:self.desktop.pin_menu(menu,entry)
   menu.addSeparator()
  if len(keys)==1:self.window_actions(menu,keys[0])
  else:
   for key in keys:
    w=self.desktop.windows.get(key)
    if w is not None:self.window_actions(menu.addMenu(w.windowTitle()),key)
  return menu
 def options(self):
  menu=QMenu(self)
  for title,key,default in [('Show all workspaces','running_current_only',False),('Group windows by app','running_group',True)]:
   action=menu.addAction(title);action.setCheckable(True);value=self.desktop.settings.value(key,default,type=bool);action.setChecked(not value if key=='running_current_only' else value)
   action.toggled.connect(lambda checked,k=key:self.option(k,not checked if k=='running_current_only' else checked))
  menu.addSeparator();menu.addAction('Preferences…',self.desktop.preferences);menu.exec(self.mapToGlobal(self.rect().topRight()))
 def option(self,key,value):self.desktop.settings.setValue(key,value);self.signature=None;self.desktop.queue_running_refresh()
