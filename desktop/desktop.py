#!/usr/bin/env python3
"""MacaqueSTEP 0.23: sessions, command palette, shortcuts, and host inventory."""
import sys,os,json
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QEvent,QSize,QRect,QProcess
from PySide6.QtGui import QAction,QKeySequence,QIcon
from PySide6.QtWidgets import *
from foundation import DesktopFoundation,icon,THEMES,set_icon_theme,refresh_icon_widgets
from terminal import Terminal
from paint_app import Paint
from archives import Archives
from help_app import Help
from running_dock import RunningDock,app_kind
from overview import Overview
from search_app import Search
from host_apps import HostApps,application_entries,launch_application
from backup_app import Backups,apply_pending_restore
from system_controls import SystemControls
from project_status import ProjectStatus
from organizer import Notes
from sound_theme import SoundTheme,SoundPreferences,SoundEvents
from about_app import About,SettingsHub,VERSION
from PySide6.QtCore import QSettings,QLockFile
from storage import data_root
from wm_features import WMFeatures,FocusEvents
from drawers import DrawerEditor,load_drawers,launch_entry
from session_tools import SessionTools,load_profiles
from command_center import Commands
from unix_readiness import Readiness
from dock_workspace import DockWorkspace
from wmaker_behavior import WMBehavior,TitleEvents
from pinning import Pinning
from desktop_layout import DesktopLayout
from service_panels import ModernServices
from workstation_tools import WorkstationTools
class Desktop(WorkstationTools,ModernServices,DesktopLayout,Pinning,WMBehavior,DockWorkspace,SessionTools,Commands,WMFeatures,DesktopFoundation):
 def __init__(self):
  self._sounds_ready=False;self.workspace=0;self.switching=False;self.exiting=False;self._running_refresh_pending=False
  try:apply_pending_restore(QSettings('MacaqueSTEP','DesktopPreview'))
  except Exception as error:QMessageBox.warning(None,'Restore failed',str(error)+'\nThe restore was left pending; your current desktop can still open.')
  defaults=QSettings('MacaqueSTEP','DesktopPreview')
  if not defaults.value('single_dock_default_v22',False,type=bool):defaults.setValue('dock_fit',False);defaults.setValue('single_dock_default_v22',True)
  super().__init__();self.setWindowTitle('MacaqueSTEP 0.23 — Desktop Preview')
  self.workspace_buttons=[];top=self.centralWidget().layout().itemAt(0).widget().layout()
  for i in range(4):
   b=QPushButton(str(i+1));b.setObjectName('workspaceButton');b.setFixedWidth(35);b.setCheckable(True);b.setToolTip('Workspace '+str(i+1));b.clicked.connect(lambda checked=False,n=i:self.switch_workspace(n));top.insertWidget(2+i,b);self.workspace_buttons.append(b)
   a=QAction(self);a.setShortcut(QKeySequence('Ctrl+Alt+'+str(i+1)));a.triggered.connect(lambda checked=False,n=i:self.switch_workspace(n));self.addAction(a)
  for key,title,fn in [('paint','Paint',self.paint_app),('archive','Archive Viewer',self.archives),('help','Help',self.help_center),('search','File Search',self.search_files),('host-apps','Installed Apps',self.host_apps),('backups','Backups',self.backups),('controls','System Controls',self.system_controls)]:
   b=QPushButton();b.setObjectName('dock');b.setIcon(icon(key));b.setToolTip(title);b.clicked.connect(fn);layout=self.dock_scroll.widget().layout();layout.insertWidget(layout.count()-1,b);self.dock_buttons[key]=b
  overview_button=QPushButton('Overview');overview_button.setToolTip('Workspace Overview • Ctrl+Alt+O');overview_button.clicked.connect(self.overview);top.insertWidget(6,overview_button)
  self.apply_dock_size(int(self.settings.value('dock_size',48)))
  self.running_dock=RunningDock(self);self.running_dock.setParent(self.area.viewport());self.area.viewport().installEventFilter(self);self.switch_workspace(0);self.apply_theme(self.theme);self.queue_running_refresh()
  for shortcut,fn in [('Ctrl+Alt+O',self.overview),('Ctrl+Alt+F',self.search_files),('Ctrl+Alt+Shift+Left',lambda:self.snap_active('Left')),('Ctrl+Alt+Shift+Right',lambda:self.snap_active('Right')),('Ctrl+Alt+Shift+Up',lambda:self.snap_active('Top')),('Ctrl+Alt+Shift+Down',lambda:self.snap_active('Bottom'))]:
   action=QAction(self);action.setShortcut(QKeySequence(shortcut));action.triggered.connect(fn);self.addAction(action)
  self.sounds=SoundTheme(self.settings,self);self.sound_events=SoundEvents(self);QApplication.instance().installEventFilter(self.sound_events);QApplication.instance().aboutToQuit.connect(self.sounds.shutdown)
  self.focus_events=FocusEvents(self);QApplication.instance().installEventFilter(self.focus_events);self.area.subWindowActivated.connect(self.enforce_stacking)
  self.drawer_button=QPushButton('Drawers');self.drawer_button.setToolTip('Launcher drawers • Ctrl+Alt+D');top.insertWidget(7,self.drawer_button);self.refresh_drawer_menu();self.refresh_workspace_names()
  self.drawer_tile=QPushButton();self.drawer_tile.setObjectName('dock');self.drawer_tile.setIcon(icon('drawers'));self.drawer_tile.setToolTip('Launcher drawers');layout=self.dock_scroll.widget().layout();layout.insertWidget(layout.count()-1,self.drawer_tile);self.dock_buttons['drawers']=self.drawer_tile;self.refresh_drawer_menu();self.apply_dock_size(int(self.settings.value('dock_size',48)))
  for i,button in enumerate(self.workspace_buttons):button.setContextMenuPolicy(Qt.CustomContextMenu);button.customContextMenuRequested.connect(lambda pos,n=i:self.rename_workspace(n))
  for shortcut,callback in [('Ctrl+Alt+S',self.shade_active),('Ctrl+Alt+D',self.open_drawers),('Ctrl+Alt+PgDown',lambda:self.switch_workspace((self.workspace+1)%4)),('Ctrl+Alt+PgUp',lambda:self.switch_workspace((self.workspace-1)%4))]:
   action=QAction(self);action.setShortcut(QKeySequence(shortcut));action.triggered.connect(callback);self.addAction(action)
  self.setup_commands()
  self.command_button=QPushButton('Commands');self.command_button.setToolTip('Search desktop actions, apps, and windows');self.command_button.clicked.connect(self.command_palette);top.insertWidget(8,self.command_button)
  self.setup_workspace_docks()
  self.title_events=TitleEvents(self)
  for key,w in self.windows.items():w.titlebar.setProperty('wm_title_key',key);w.titlebar.installEventFilter(self.title_events)
  self.setup_app_menu()
  self.apply_accessibility()
  QTimer.singleShot(600,self.maybe_open_setup)
 def readiness_panel(self):
  if 'unix-readiness' in self.windows:self.reopen('unix-readiness');return
  self.window('unix-readiness','Unix Readiness — Host Inventory',Readiness(),(100,50,780,590))
 def play_sound(self,event):
  if self._sounds_ready and hasattr(self,'sounds') and not self.exiting:return self.sounds.play(event)
  return False
 def sound_preferences(self):
  if 'sounds' in self.windows:self.reopen('sounds');return
  self.window('sounds','Sound Effects',SoundPreferences(self.sounds),(120,70,600,590))
 def settings_hub(self):
  if 'settings-hub' in self.windows:self.reopen('settings-hub');return
  self.window('settings-hub','MacaqueSTEP Settings',SettingsHub(self),(120,80,670,570))
 def about_tab(self,index):
  self.about();self.windows['about'].content.tabs.setCurrentIndex(index)
 def reset_layout(self):
  super().reset_layout()
  if 'about' in self.windows:
   w=self.windows['about'];r=self.work_rect();w.resize(min(760,max(300,r.width()-30)),min(570,max(160,r.height()-25)));w.move(max(0,(r.width()-w.width())//2),15);self.ensure_visible(w)
 def apply_theme(self,name):
  set_icon_theme(name);super().apply_theme(name)
  bg,panel,fg,line,field=THEMES[self.theme]
  self.setStyleSheet(self.styleSheet()+f'QPushButton#workspaceButton:checked {{background:#21b9ad;color:#082e31;border:1px solid #41e1d0;font-weight:700;}} QFrame#runningDock {{background:{panel};border-top:1px solid {line};}} QWidget#runningPanel,QScrollArea#runningScroll {{background:{panel};border:0;}} QToolButton#runningTile {{background:{panel};color:{fg};border:1px solid {line};border-radius:5px;padding:3px;font-size:11px;}} QToolButton#runningTile:hover {{border:1px solid #21b9ad;}} QToolButton#runningTile[activeApp="true"] {{border-bottom:3px solid #21b9ad;background:{field};}} QPushButton#dock[runningApp="true"] {{border-bottom:3px solid #21b9ad;}} QToolButton#runningOptions {{background:{panel};color:{fg};border:1px solid {line};padding:5px;}}')
  self.queue_running_refresh()
  self.setStyleSheet(self.styleSheet()+f'QFrame#runningDock,QWidget#runningPanel,QScrollArea#runningScroll {{background:transparent;border:0;}} QToolButton#runningTile {{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {panel},stop:1 {bg});border:1px solid {line};border-top:1px solid #91a0ac;border-radius:7px;padding:7px;}} QToolButton#runningTile:hover {{background:{line};border:1px solid #2cc9bd;}} QToolButton#runningTile[activeApp="true"] {{border-bottom:3px solid #21b9ad;}} QScrollArea#preferencesScroll,QWidget#preferencesContent {{background:{panel};border:0;}} QTableView,QTableWidget {{background:{field};alternate-background-color:{panel};color:{fg};gridline-color:{line};}} QHeaderView::section,QTableCornerButton::section {{background:{panel};color:{fg};border:1px solid {line};padding:4px;}} QDialog,QGroupBox {{background:{panel};color:{fg};}}')
  self.setStyleSheet(self.styleSheet()+f'QWidget#aboutPage,QTabWidget::pane {{background:{panel};color:{fg};border:0;}} QTabBar::tab {{background:{bg};color:{fg};padding:8px 15px;border:1px solid {line};}} QTabBar::tab:selected {{background:{panel};border-bottom:2px solid #21b9ad;}}')
  self.setStyleSheet(self.styleSheet()+f'QWidget#drawerShelfBody {{background:{panel};color:{fg};}} QToolButton#clipNav {{background:{panel};color:{fg};border:1px solid {line};border-radius:3px;padding:4px;}} QToolButton#clipNav:hover {{border:1px solid #21b9ad;}}')
  self.setStyleSheet(self.styleSheet()+'QPushButton#dock,QToolButton#runningTile {padding:2px;}')
  if self.theme=='Classic':self.setStyleSheet(self.styleSheet()+'QPushButton#dock,QToolButton#runningTile {border-radius:0;border:2px outset #deded8;background:#aaa9a2;} QPushButton#dock:pressed,QToolButton#runningTile:pressed {border:2px inset #deded8;}')
  self.setStyleSheet(self.styleSheet()+f'QFrame#classicMenuBar,QWidget#classicMenus {{background:{panel};color:{fg};border:0;}} QToolButton[classicMenuButton="true"] {{border:0;border-radius:0;background:transparent;color:{fg};padding:4px 8px;}} QToolButton[classicMenuButton="true"]:hover,QToolButton[classicMenuButton="true"]:pressed {{background:#21b9ad;color:#092c31;}}')
  self.setStyleSheet(self.styleSheet()+'QToolButton[classicMenuButton="true"]::menu-indicator {image:none;width:0;height:0;}')
  self.setStyleSheet(self.styleSheet()+f'QFrame#sideAppMenu {{background:{panel};border:1px solid {line};}} QLabel#sideAppMenuTitle {{background:#15191d;color:#f4f4ef;font-weight:bold;padding:3px 6px;}} QWidget#sideMenuBody,QScrollArea#sideMenuScroll {{background:{panel};border:0;}} QPushButton#sideAppMenuRow {{text-align:left;background:{panel};color:{fg};border:0;border-bottom:1px solid {line};border-radius:0;padding:3px 7px;}} QPushButton#sideAppMenuRow:hover {{background:#21b9ad;color:#092c31;}} QPushButton#sideAppMenuRow:disabled {{color:#80888c;}}')
  if self.theme=='Classic':self.setStyleSheet(self.styleSheet()+'QPushButton#sideAppMenuRow {border:1px outset #deded8;}')
  from decorations import apply_decorations
  apply_decorations(self)
  self.apply_accessibility()
  refresh_icon_widgets(self)
  if hasattr(self,'clip'):
   self.clip.anchor.setIcon(icon('clip'));self.refresh_docks()
  if hasattr(self,'windows') and 'about' in self.windows:
   picture=self.windows['about'].content.findChild(QLabel,'aboutLogo')
   if picture:picture.setPixmap(icon('monkey').pixmap(104,104))
 def position_running_dock(self):
  if self.exiting or not hasattr(self,'running_dock'):return
  dock=self.running_dock;size=dock.tile_size();width=min(max(0,self.area.viewport().width()-20),max(1,len(dock.buttons))*(size+8)-8)
  dock.setGeometry(10,max(0,self.area.viewport().height()-size-10),max(1,width),size);dock.setVisible(self.settings.value('running_visible',True,type=bool) and bool(dock.buttons));dock.raise_()
  if hasattr(self,'clip'):self.clip.raise_()
  if hasattr(self,'side_app_menu') and self.side_app_menu.isVisible():self.side_app_menu.raise_()
  self.fit_maximized_windows()
 def fit_maximized_windows(self):
  rect=self.work_rect()
  if hasattr(self,'clip') and self.clip.isVisible():rect.setTop(min(max(0,rect.height()-160),self.clip.anchor.height()+16))
  for window in self.windows.values():
   if window.isMaximized() and not window.isMinimized() and window.geometry()!=rect:window.setGeometry(rect)
 def work_rect(self):
  r=self.area.viewport().rect();reserve=self.running_dock.tile_size()+20 if hasattr(self,'running_dock') and self.settings.value('running_visible',True,type=bool) else 0
  return QRect(0,0,r.width(),max(160,r.height()-reserve))
 def ensure_visible(self,w):
  r=self.work_rect();w.resize(min(w.width(),max(300,r.width()-10)),min(w.height(),max(160,r.height()-10)));w.move(max(0,min(w.x(),r.width()-w.width())),max(0,min(w.y(),r.height()-w.height())))
 def resizeEvent(self,event):
  super().resizeEvent(event)
  if hasattr(self,'running_dock'):self.position_running_dock()
  if hasattr(self,'side_grid'):self.fit_side_dock()
  if hasattr(self,'clip'):self.clip.refresh()
 def apply_dock_size(self,size):
  super().apply_dock_size(size)
  if hasattr(self,'side_grid'):self.refresh_docks()
  if hasattr(self,'running_dock'):self.running_dock.signature=None;self.queue_running_refresh()
 def overview(self):
  dialog=Overview(self);dialog.exec()
 def snap_active(self,position):
  w=self.area.activeSubWindow()
  if w is not None:
   key=w.property('running_key')
   if key in self.windows:self.snap_window(key,position)
 def snap_window(self,key,position):
  if key not in self.windows:return
  w=self.windows[key]
  if w.property('shaded'):self.set_shaded(key,False)
  if position=='Restore geometry':
   rect=w.property('before_snap')
   if rect is not None:w.showNormal();w.setGeometry(rect);w.setProperty('before_snap',None);self.ensure_visible(w)
   return
  if w.property('before_snap') is None:
   rect=w.property('normal_rect') if w.isMaximized() else w.geometry()
   w.setProperty('before_snap',rect if isinstance(rect,QRect) and rect.isValid() else w.geometry())
  self.reopen(key);r=self.work_rect();half_w=r.width()//2;half_h=r.height()//2
  regions={'Left':QRect(0,0,half_w,r.height()),'Right':QRect(half_w,0,r.width()-half_w,r.height()),'Top':QRect(0,0,r.width(),half_h),'Bottom':QRect(0,half_h,r.width(),r.height()-half_h),'Top left':QRect(0,0,half_w,half_h),'Top right':QRect(half_w,0,r.width()-half_w,half_h),'Bottom left':QRect(0,half_h,half_w,r.height()-half_h),'Bottom right':QRect(half_w,half_h,r.width()-half_w,r.height()-half_h)}
  if position in regions:w.setGeometry(regions[position]);self.ensure_visible(w)
  self.queue_running_refresh()
 def window(self,key,title,widget,rect):
  existed=key in self.windows
  if existed and not self.windows[key].property('sticky'):self.switch_workspace(self.windows[key].property('workspace') or 0)
  w=super().window(key,title,widget,rect)
  if not existed:
   w.destroyed.connect(lambda *_:self.play_sound('close'));self.play_sound('open');w.setProperty('workspace',self.workspace);w.setProperty('running_key',key);w.installEventFilter(self);w.windowTitleChanged.connect(self.queue_running_refresh);w.windowStateChanged.connect(self.queue_running_refresh);w.destroyed.connect(self.queue_running_refresh);w.titlebar.setContextMenuPolicy(Qt.CustomContextMenu);w.titlebar.customContextMenuRequested.connect(lambda pos,win=w:self.window_menu(win,pos))
   for kind,cls in [('paint',Paint),('archive',Archives),('terminal',Terminal)]:
    if isinstance(widget,cls):w.titlebar.findChildren(QLabel)[0].setPixmap(icon(kind).pixmap(20,20))
  if not existed:
   original=w.titlebar.mouseDoubleClickEvent
   w.titlebar.mouseDoubleClickEvent=lambda event,k=key:self.titlebar_double_click(k,event)
   if hasattr(self,'title_events'):w.titlebar.setProperty('wm_title_key',key);w.titlebar.installEventFilter(self.title_events)
   controls=w.titlebar.findChildren(QPushButton)
   if len(controls)>=2:
    controls[0].clicked.disconnect();controls[0].clicked.connect(lambda checked=False,k=key:self.minimize_running(k));controls[1].clicked.disconnect();controls[1].clicked.connect(lambda checked=False,k=key:self.maximize_running(k))
   self.apply_window_rule(key,w)
  from decorations import decorate
  decorate(self,w)
  self.enforce_stacking();return w
 def startup(self):
  if self.exiting:return
  super().startup()
  try:spaces=json.loads(self.settings.value('core_spaces_v05','{}'))
  except (ValueError,TypeError):spaces={}
  for key,n in spaces.items():
   if key in self.windows and type(n)==int and 0<=n<4:self.windows[key].setProperty('workspace',n)
  for key,w in list(self.windows.items()):self.apply_window_rule(key,w)
  self.switch_workspace(0)
  profile=load_profiles(self.settings).get(self.settings.value('session_startup',''))
  if profile is not None:self.apply_layout(profile,open_missing=True,remember=False)
  self._sounds_ready=True
  QTimer.singleShot(200,lambda:self.play_sound('startup'))
 def switch_workspace(self,n):
  if not 0<=n<4:return
  changed=self.workspace!=n
  self.switching=True;self.workspace=n
  for w in self.windows.values():
   if ((w.property('workspace') or 0)==n or w.property('sticky')) and not w.isMinimized() and not w.property('app_hidden'):w.show()
   else:w.hide()
  for i,b in enumerate(getattr(self,'workspace_buttons',[])):b.setChecked(i==n)
  self.switching=False;self.update_tasks()
  if changed:self.play_sound('workspace')
  self.enforce_stacking()
  if hasattr(self,'clip'):self.clip.refresh()
 def reopen(self,key):
  if key in self.windows and self.windows[key].property('app_hidden'):self.unhide_application(key)
  if key in self.windows and not self.windows[key].property('sticky'):self.switch_workspace(self.windows[key].property('workspace') or 0)
  super().reopen(key)
 def move_workspace(self,w,n):
  w.setProperty('workspace',n);w.setProperty('sticky',False);self.switch_workspace(self.workspace)
 def center_preview_window(self,w):
  r=self.work_rect();w.move(max(0,(r.width()-w.width())//2),max(0,(r.height()-w.height())//2));self.ensure_visible(w)
 def resize_preview_window(self,w,width,height):
  key=w.property('running_key')
  if w.property('shaded'):self.set_shaded(key,False)
  w.showNormal();r=self.work_rect();w.resize(min(width,r.width()),min(height,r.height()));self.center_preview_window(w)
 def window_menu(self,w,pos):
  menu=QMenu(self);menu.addAction('Minimize',w.showMinimized);menu.addAction('Maximize / Restore',lambda:self.maximize_running(w.property('running_key')));sub=menu.addMenu('Move to workspace')
  for i in range(4):sub.addAction('Workspace '+str(i+1),lambda checked=False,n=i:self.move_workspace(w,n))
  snap=menu.addMenu('Snap window')
  for position in ['Left','Right','Top','Bottom','Top left','Top right','Bottom left','Bottom right','Restore geometry']:snap.addAction(position,lambda checked=False,p=position:self.snap_window(w.property('running_key'),p))
  menu.addAction('Center window',lambda:self.center_preview_window(w))
  sizes=menu.addMenu('Window size')
  for title,width,height in [('Compact',480,320),('Comfortable',800,560),('Large',1100,760)]:sizes.addAction(title,lambda checked=False,x=width,y=height:self.resize_preview_window(w,x,y))
  self.wm_actions(menu,w.property('running_key'));menu.addSeparator();menu.addAction('Workspace overview…',self.overview);menu.addAction('Close',w.close);menu.exec(w.titlebar.mapToGlobal(pos))
 def terminal(self):
  if 'terminal' in self.windows:self.reopen('terminal');self.windows['terminal'].content.view.setFocus();return
  try:box=Terminal()
  except (OSError,ImportError) as e:QMessageBox.warning(self,'Terminal',str(e));return
  self.window('terminal','Interactive Terminal',box,(30,470,850,360));box.view.setFocus()
 def paint_app(self):
  if 'paint' in self.windows:self.reopen('paint');return
  self.window('paint','Paint',Paint(),(70,70,1000,650))
 def archives(self,path=None):
  if isinstance(path,bool):path=None
  if 'archive' in self.windows:
   self.reopen('archive')
   if path:self.windows['archive'].content.load(path)
   return
  self.window('archive','Archive Viewer',Archives(path),(120,70,820,500))
 def help_center(self):
  if 'help' in self.windows:self.reopen('help');return
  self.window('help','MacaqueSTEP Help',Help(),(100,60,850,550))
 def open_path(self,p):
  name=str(p).lower()
  if name.endswith(('.zip','.tar','.tar.gz','.tgz','.tar.xz','.tar.bz2')):self.archives(p);self.remember_document(p)
  else:super().open_path(p)
 def about(self):
  if 'about' in self.windows:self.reopen('about');return
  self.window('about','About MacaqueSTEP',About(self),(160,60,760,570))
 def network_settings(self):
  from network_app import NetworkPanel
  if 'network' in self.windows:self.reopen('network');return
  self.window('network','Wi-Fi & Network',NetworkPanel(self),(120,70,640,480))
 def launcher(self):
  if 'launcher' in self.windows:self.reopen('launcher');return
  entries=[('File Viewer',self.files),('Interactive Terminal',self.terminal),('Text Editor',self.editor),('Notes',self.notes),('Tasks',self.tasks),('Paint',self.paint_app),('Image Viewer',self.images),('Media Player',self.media),('Archive Viewer',self.archives),('Calculator',self.calculator),('Clock & Timer',self.clock_app),('System Information',self.system_info),('Preferences',self.preferences),('Screenshot',self.screenshot),('Open Windows',self.window_list),('Workspace Overview',self.overview),('File Search',self.search_files),('Installed Applications',self.host_apps),('Wi-Fi & Network',self.network_settings),('System Controls',self.system_controls),('Backups',self.backups),('Project Status',self.project_status),('Sound Effects',self.sound_preferences),('Settings Hub',self.settings_hub),('Window Rules',self.rules_panel),('Launcher Drawers',self.open_drawers),('Desktop Sessions',self.sessions_panel),('Keyboard Shortcuts',self.shortcuts_panel),('Command Palette',self.command_palette),('Unix Readiness Inventory',self.readiness_panel),('Drawer Shelf',self.drawer_shelf),('Help',self.help_center),('About MacaqueSTEP',self.about)]
  from command_center import TOOLS
  known={fn.__name__ for _,fn in entries}
  entries.extend((title,getattr(self,method)) for title,method in TOOLS if method not in known)
  builtins=list(entries)
  native=application_entries()
  entries.extend((entry['name'],lambda path=entry['path']:launch_application(self,path)) for entry in native)
  box=QWidget();v=QVBoxLayout(box);search=QLineEdit();search.setPlaceholderText('Search applications and desktop tools…');items=QListWidget();v.addWidget(search);v.addWidget(items)
  for name,fn in entries:items.addItem(name)
  for index,entry in enumerate(native,start=len(entries)-len(native)):
   item=items.item(index);item.setToolTip(entry['comment'] or 'Installed application')
   item.setIcon(QIcon(entry['icon']) if entry['icon'].startswith('/') else QIcon.fromTheme(entry['icon']))
  status=QLabel(f'{len(native)} installed applications • {len(entries)-len(native)} desktop tools');v.addWidget(status)
  def filter_items(s):
   for i in range(items.count()):items.item(i).setHidden(s.lower() not in items.item(i).text().lower())
  def first():
   for i in range(items.count()):
    if not items.item(i).isHidden():entries[i][1]();return
  items.setContextMenuPolicy(Qt.CustomContextMenu)
  def pin_context(pos):
   item=items.itemAt(pos)
   if item is None:return
   entry=self.entry_for_callback(entries[items.row(item)][1])
   if entry:
    menu=QMenu(self);self.pin_menu(menu,entry);menu.exec(items.mapToGlobal(pos))
  items.customContextMenuRequested.connect(pin_context)
  refresh=QPushButton('Refresh applications');v.addWidget(refresh)
  def reload_apps():
   native=application_entries()
   entries[:]=builtins+[(entry['name'],lambda path=entry['path']:launch_application(self,path)) for entry in native]
   items.clear()
   for name,fn in entries:items.addItem(name)
   for index,entry in enumerate(native,start=len(builtins)):
    items.item(index).setToolTip(entry['comment'] or 'Installed application')
    items.item(index).setIcon(QIcon(entry['icon']) if entry['icon'].startswith('/') else QIcon.fromTheme(entry['icon']))
   status.setText(f'{len(native)} installed applications • {len(builtins)} desktop tools');filter_items(search.text())
  refresh.clicked.connect(reload_apps)
  search.textChanged.connect(filter_items);search.returnPressed.connect(first);items.itemActivated.connect(lambda item:entries[items.row(item)][1]());self.window('launcher','Applications',box,(120,60,450,600));search.setFocus()
 def window_list(self):
  if 'window-list' in self.windows:self.reopen('window-list');return
  box=QWidget();v=QVBoxLayout(box);items=QListWidget();v.addWidget(items)
  def activate(item):
   key=item.data(Qt.UserRole)
   if key in self.windows:self.reopen(key)
  items.itemActivated.connect(activate);row=QHBoxLayout()
  for name,fn in [('Tile this workspace',self.tile_workspace),('Cascade this workspace',self.cascade_workspace),('Restore core layout',self.reset_layout)]:b=QPushButton(name);b.clicked.connect(fn);row.addWidget(b)
  v.addLayout(row);self.window('window-list','Open Windows — All Workspaces',box,(100,80,620,450));self.update_tasks()
 def update_tasks(self,*_):
  self.queue_running_refresh()
  if not hasattr(self,'windows') or 'window-list' not in self.windows:return
  items=self.windows['window-list'].content.findChild(QListWidget);items.clear()
  for key,w in self.windows.items():
   if key=='window-list':continue
   item=QListWidgetItem('['+('All workspaces' if w.property('sticky') else self.workspace_name(w.property('workspace') or 0))+']  '+w.windowTitle()+(' · shaded' if w.property('shaded') else '')+(' · minimized' if w.isMinimized() else ''));item.setData(Qt.UserRole,key);items.addItem(item)
 def tile_workspace(self):self.arrange_windows('tile')
 def cascade_workspace(self):self.arrange_windows('cascade')
 def eventFilter(self,obj,event):
  if self.exiting:return False
  if event.type()==QEvent.Resize and obj is self.area.viewport():
   QTimer.singleShot(0,self.position_running_dock)
   if hasattr(self,'side_app_menu'):QTimer.singleShot(0,self.update_side_menu_geometry)
  if event.type()==QEvent.Resize and hasattr(self,'dock_scroll') and obj is self.dock_scroll.viewport() and hasattr(self,'side_grid'):QTimer.singleShot(0,self.fit_side_dock)
  if event.type()==QEvent.WindowStateChange and hasattr(obj,'content'):
   if obj.isMinimized():
    self.play_sound('minimize')
    if event.oldState() & Qt.WindowMaximized:obj.setProperty('restore_maximized',True)
    QTimer.singleShot(0,lambda key=obj.property('running_key'):self.hide_minimized(key))
   elif event.oldState() & Qt.WindowMinimized:self.play_sound('restore')
   self.queue_running_refresh()
  if event.type()==QEvent.Close and hasattr(obj,'content'):
   content=obj.content
   if isinstance(content,(Search,SystemControls)) and not content.shutdown():event.ignore();return True
   if isinstance(content,Paint) and not self.exiting and not content.discard():event.ignore();return True
   if isinstance(content,Terminal):content.shutdown()
   if isinstance(content,Archives):content.shutdown()
  return super().eventFilter(obj,event)
 def queue_running_refresh(self,*_):
  if self.exiting or self._running_refresh_pending:return
  self._running_refresh_pending=True;QTimer.singleShot(0,self.refresh_running)
 def refresh_running(self):
  self._running_refresh_pending=False
  if self.exiting or not hasattr(self,'running_dock'):return
  self.running_dock.sync();self.position_running_dock()
  kinds={app_kind(key) for key in self.windows}
  mapping={'monkey':'about','settings':'preferences','apps':'launcher','windows':'window-list','images':'image'}
  for key,button in self.dock_buttons.items():
   running=mapping.get(key,key) in kinds
   if button.property('runningApp')!=running:
    button.setProperty('runningApp',running);button.style().unpolish(button);button.style().polish(button)
 def hide_minimized(self,key):
  if key in self.windows and self.windows[key].isMinimized():
   self.windows[key].hide()
   if self.area.activeSubWindow() is None:
    for candidate in reversed(self.area.subWindowList(QMdiArea.ActivationHistoryOrder)):
     if candidate.isVisible() and not candidate.isMinimized() and ((candidate.property('workspace') or 0)==self.workspace or candidate.property('sticky')):self.area.setActiveSubWindow(candidate);break
   self.queue_running_refresh()
 def activate_running(self,key,toggle=True):
  if key not in self.windows:return
  w=self.windows[key];active=self.area.activeSubWindow() is w and w.isVisible() and not w.isMinimized() and ((w.property('workspace') or 0)==self.workspace or w.property('sticky'))
  if active and toggle:self.minimize_running(key);return
  was_minimized=w.isMinimized();restore_max=bool(w.property('restore_maximized'))
  self.reopen(key)
  if was_minimized and restore_max:w.showMaximized()
  self.area.setActiveSubWindow(w);self.queue_running_refresh()
 def minimize_running(self,key):
  if key in self.windows:
   w=self.windows[key]
   if w.isMinimized():return
   rect=w.property('normal_rect') if w.isMaximized() else w.geometry()
   if not isinstance(rect,QRect) or not rect.isValid():rect=w.geometry()
   w.setProperty('before_minimize',rect);w.setProperty('restore_maximized',w.isMaximized());w.showMinimized();self.queue_running_refresh()
 def maximize_running(self,key):
  if key not in self.windows:return
  w=self.windows[key]
  if w.property('shaded'):self.set_shaded(key,False)
  was_max=w.isMaximized();self.reopen(key)
  if not was_max:w.setProperty('normal_rect',w.geometry());w.showMaximized()
  self.queue_running_refresh()
 def move_running(self,key,n):
  if key in self.windows:self.move_workspace(self.windows[key],n);self.queue_running_refresh()
 def preferences(self):
  if 'preferences' in self.windows:self.reopen('preferences');return
  super().preferences();w=self.windows['preferences'];box=w.content;form=box.layout()
  for label,fn in [('Setup Assistant…',self.setup_assistant),('Software Center…',self.software_center),('Accessibility…',self.accessibility_panel),('Lock & Sleep…',self.lock_sleep),('Personal Backup & Recovery…',self.personal_recovery)]:
   button=QPushButton(label);button.clicked.connect(fn);form.addRow(button)
  from os_integration import available,install_system
  if available():
   installer=QPushButton('Install MacaqueSTEP to disk…');installer.clicked.connect(lambda:install_system(self));form.addRow(installer)
  from decorations import decoration_preferences
  decoration_preferences(self,form)
  repair=QPushButton('Show File / Edit Menus Now');repair.setObjectName('restoreClassicMenus');repair.clicked.connect(self.show_classic_menus);form.addRow(repair)
  style=QComboBox();style.setObjectName('desktopBarStyle')
  for title,value in [('Classic app menu bar','classic'),('Desktop toolbar','toolbar'),('Floating app menu (no top bar)','none')]:style.addItem(title,value)
  style.setCurrentIndex(style.findData(self.bar_style()));style.currentIndexChanged.connect(lambda _:self.set_bar_style(style.currentData()));form.addRow('Menu bar layout',style)
  topbar=QCheckBox('Show horizontal top bar');topbar.setObjectName('topBarVisibility');topbar.setChecked(self.top_bar_visible());topbar.toggled.connect(self.set_top_bar_visible);form.addRow(topbar)
  side_menu=QCheckBox('Show movable app menu when top bar is off');side_menu.setChecked(self.settings.value('left_menu_enabled',True,type=bool));side_menu.toggled.connect(lambda checked:(self.settings.setValue('left_menu_enabled',checked),self.sync_side_app_menu(),self.update_desktop_layout()));form.addRow(side_menu)
  fit=QCheckBox('Allow extra dock columns (fit without scrolling)');fit.setChecked(self.settings.value('dock_fit',False,type=bool));fit.toggled.connect(lambda checked:(self.settings.setValue('dock_fit',checked),self.fit_side_dock(),self.clip.refresh()));form.addRow(fit)
  visible=QCheckBox('Show workspace Clip');visible.setChecked(self.settings.value('clip_visible',True,type=bool));visible.toggled.connect(lambda checked:(self.settings.setValue('clip_visible',checked),self.clip.refresh()));form.addRow(visible)
  launching=QCheckBox('Double-click dock icons to launch (Window Maker style)');launching.setChecked(self.settings.value('dock_double_click',False,type=bool));launching.toggled.connect(lambda checked:self.settings.setValue('dock_double_click',checked));form.addRow(launching)
  restore=QPushButton('Restore default side-dock launchers');restore.clicked.connect(self.restore_side_launchers);form.addRow(restore)
  for title,fn in [('Drawer Shelf…',self.drawer_shelf),('All Settings…',self.settings_hub),('Sound Effects…',self.sound_preferences),('Window Rules…',self.rules_panel),('Launcher Drawers…',self.open_drawers)]:button=QPushButton(title);button.clicked.connect(fn);form.addRow(button)
  for title,key,default in [('Show running-app dock','running_visible',True),('Match running tiles to side dock size','running_follow_side',True),('Group windows by application','running_group',True),('Only show the current workspace','running_current_only',False)]:
   check=QCheckBox(title);check.setChecked(self.settings.value(key,default,type=bool));check.toggled.connect(lambda checked,k=key:self.set_running_option(k,checked));form.addRow(check)
  size=QSlider(Qt.Horizontal);size.setRange(24,56);size.setValue(int(self.settings.value('running_icon_size',36)));size.valueChanged.connect(lambda n:self.set_running_option('running_icon_size',n));form.addRow('Independent running icon size',size)
  size.setDisabled(self.settings.value('running_follow_side',True,type=bool))
  for check in box.findChildren(QCheckBox):
   if check.text()=='Match running tiles to side dock size':check.toggled.connect(size.setDisabled)
  focus=QCheckBox('Focus follows mouse');focus.setChecked(self.settings.value('wm_focus_follows_mouse',False,type=bool));focus.toggled.connect(lambda value:self.settings.setValue('wm_focus_follows_mouse',value));form.addRow(focus)
  raise_focus=QCheckBox('Raise windows when focused by mouse');raise_focus.setChecked(self.settings.value('wm_raise_on_focus',False,type=bool));raise_focus.toggled.connect(lambda value:self.settings.setValue('wm_raise_on_focus',value));form.addRow(raise_focus)
  double_click=QComboBox();double_click.addItems(['Shade','Maximize']);double_click.setCurrentText(self.settings.value('wm_double_click','Shade'));double_click.currentTextChanged.connect(lambda value:self.settings.setValue('wm_double_click',value));form.addRow('Title-bar double-click',double_click)
  outer=w.widget().layout();outer.removeWidget(box);scroll=QScrollArea();scroll.setObjectName('preferencesScroll');box.setObjectName('preferencesContent');scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame);scroll.setWidget(box);outer.insertWidget(1,scroll);w.resize(530,640);self.ensure_visible(w)
 def set_running_option(self,key,value):
  self.settings.setValue(key,value)
  if hasattr(self,'running_dock'):self.running_dock.signature=None
  self.queue_running_refresh()
 def search_files(self):
  if 'search' in self.windows:self.reopen('search');return
  self.window('search','File Search',Search(self),(100,80,820,520))
 def host_apps(self):
  if 'host-apps' in self.windows:self.reopen('host-apps');return
  self.window('host-apps','Installed Applications',HostApps(),(120,70,650,560))
 def system_controls(self):
  if 'controls' in self.windows:self.reopen('controls');return
  self.window('controls','System Controls',SystemControls(),(120,80,650,520))
 def backups(self):
  if 'backups' in self.windows:self.reopen('backups');return
  self.window('backups','Backups & Restore',Backups(self),(150,90,650,400))
 def project_status(self):
  if 'project-status' in self.windows:self.reopen('project-status');return
  self.window('project-status','Project Status & OS Readiness',ProjectStatus(),(60,50,1050,620))
 def flush_notes(self):
  for w in self.windows.values():
   if isinstance(w.content,Notes) and not w.content.flush():return False
  return True
 def shade_active(self):
  w=self.area.activeSubWindow()
  if w is not None:self.set_shaded(w.property('running_key'),not bool(w.property('shaded')))
 def open_drawers(self):
  if 'drawers' in self.windows:self.reopen('drawers');return
  self.window('drawers','Launcher Drawers',DrawerEditor(self),(80,70,900,500))
 def refresh_drawer_menu(self):
  if not hasattr(self,'drawer_button'):return
  previous=self.drawer_button.menu();menu=QMenu(self.drawer_button)
  for drawer in load_drawers(self.settings):
   submenu=menu.addMenu(drawer['name'])
   for entry in drawer['entries']:submenu.addAction(entry['name'],lambda checked=False,e=entry:launch_entry(self,e))
   if not drawer['entries']:action=submenu.addAction('(Empty drawer)');action.setEnabled(False)
  menu.addSeparator();menu.addAction('Customize drawers…',self.open_drawers);self.drawer_button.setMenu(menu)
  if hasattr(self,'drawer_tile') and not hasattr(self,'clip'):self.drawer_tile.setMenu(menu)
  if previous:previous.deleteLater()
 def closeEvent(self,event):
  from os_integration import installer_center_open
  installer_process=getattr(self,'_installer_center_process',None)
  if installer_center_open() or (installer_process is not None and installer_process.state()!=QProcess.NotRunning):QMessageBox.information(self,'Installer Center open','Finish or cancel in Calamares, then close Installer Center before ending this desktop session.');event.ignore();return
  for w in list(self.windows.values()):
   if hasattr(w.content,'can_close') and not w.content.can_close():event.ignore();return
  # Stop bounded background tools before shutting down windows.
  for w in list(self.windows.values()):
   if isinstance(w.content,(Search,SystemControls)) and not w.content.shutdown():event.ignore();return
  # Complete all prompts before terminating the interactive shell.
  for w in list(self.windows.values()):
   if isinstance(w.content,Paint) and not w.content.discard():event.ignore();return
  super().closeEvent(event)
  if not event.isAccepted():return
  self.exiting=True
  if hasattr(self,'sounds'):self.sounds.shutdown()
  self.settings.setValue('core_spaces_v05',json.dumps({key:w.property('workspace') or 0 for key,w in self.windows.items() if key in ('files','terminal','about')}))
  for w in list(self.windows.values()):
   if isinstance(w.content,(Terminal,Archives)):w.content.shutdown()
if __name__=='__main__':
 if '--version' in sys.argv:print('MacaqueSTEP '+VERSION);sys.exit(0)
 app=QApplication(sys.argv);app.setStyle('Fusion');app.setWindowIcon(icon('monkey'))
 if '--diagnose' in sys.argv:
  settings=QSettings('MacaqueSTEP','DesktopPreview');print(json.dumps({'version':VERSION,'source':str(Path(__file__).resolve()),'python':sys.executable,'menu_layout':settings.value('desktop_bar_style','classic'),'bar_visible':settings.value('top_bar_visible',True,type=bool),'menu_implementation':'embedded tool buttons','left_menu_enabled':settings.value('left_menu_enabled',True,type=bool),'menus':['MacaqueSTEP','File','Edit','View','Go','Window','Help']},indent=2));sys.exit(0)
 if os.environ.get('MACAQUESTEP_SESSION')=='1':
  defaults=QSettings('MacaqueSTEP','DesktopPreview')
  if not defaults.contains('desktop_bar_style'):defaults.setValue('desktop_bar_style','none');defaults.setValue('top_bar_visible',False)
 lock=QLockFile(str(data_root()/'preview-instance.lock'))
 if not lock.tryLock(0):QMessageBox.information(None,'MacaqueSTEP','Another MacaqueSTEP preview is already running. Close its window, then launch version '+VERSION+' again.');sys.exit(0)
 app.aboutToQuit.connect(lock.unlock);d=Desktop()
 if '--left-menu' in sys.argv:d.show_left_app_menu()
 elif '--classic-menus' in sys.argv:d.show_classic_menus()
 d.showFullScreen() if '--fullscreen' in sys.argv else d.show()
 if '--smoke-test' in sys.argv:QTimer.singleShot(700,d.close)
 sys.exit(app.exec())
