"""Persistent NeXT/GNUstep-style app menu when the horizontal bar is off."""
import json
from PySide6.QtCore import Qt,QTimer,QPoint,QRect
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import *
from running_dock import app_kind,APP_NAMES
from command_center import TOOLS
class MenuRow(QPushButton):
 def paintEvent(self,event):
  super().paintEvent(event)
  if self.property('submenuRow'):
   painter=QPainter(self);option=QStyleOption();option.initFrom(self);option.rect=QRect(self.width()-17,(self.height()-8)//2,8,8);self.style().drawPrimitive(QStyle.PE_IndicatorArrowRight,option,painter,self);painter.end()
class MenuHeader(QLabel):
 def __init__(self,panel):
  super().__init__('MacaqueSTEP',panel);self.panel=panel;self.setCursor(Qt.OpenHandCursor);self.setAccessibleName('Movable application menu title')
 def mousePressEvent(self,event):
  if event.button()==Qt.LeftButton:self.panel.begin_drag(event);event.accept()
  else:super().mousePressEvent(event)
 def mouseMoveEvent(self,event):
  if self.panel.drag_offset is not None:self.panel.drag_to(event);event.accept()
  else:super().mouseMoveEvent(event)
 def mouseReleaseEvent(self,event):
  if event.button()==Qt.LeftButton:self.panel.end_drag();event.accept()
  else:super().mouseReleaseEvent(event)
class SideAppMenu(QFrame):
 WIDTH=180
 def __init__(self,d):
  super().__init__(d.area);self.d=d;self.backend=d.app_menu;self.setObjectName('sideAppMenu');self.setFixedWidth(self.WIDTH);self.setFocusPolicy(Qt.NoFocus);v=QVBoxLayout(self);v.setContentsMargins(1,1,1,1);v.setSpacing(0);self.drag_offset=None;self.title=MenuHeader(self);self.title.setObjectName('sideAppMenuTitle');self.title.setFixedHeight(28);v.addWidget(self.title)
  scroll=QScrollArea();scroll.setObjectName('sideMenuScroll');scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);body=QWidget();body.setObjectName('sideMenuBody');rows=QVBoxLayout(body);rows.setContentsMargins(0,0,0,0);rows.setSpacing(0);self.buttons={};self.menus={}
  for label in ('Info','File','Edit','View','Go','Tools','Windows','Services','Help'):
   button=self.button(label);button.setProperty('submenuRow',True);self.buttons[label]=button;menu=QMenu(button);self.menus[label]=menu;menu.aboutToShow.connect(lambda name=label:self.populate(name));button.clicked.connect(lambda checked=False,name=label:self.open_menu(name));rows.addWidget(button)
  for name,callback in [('Applications…',d.launcher),('Wi-Fi & Network…',d.network_settings),('Hide',self.hide_app),('Hide Others',self.hide_others),('Show All',d.show_all_applications),('Print…',self.print_app),('Quit Preview',d.close)]:
   button=self.button(name);button.clicked.connect(callback);rows.addWidget(button);self.buttons[name]=button
  from os_integration import available,install_system
  if available():
   button=self.button('Install MacaqueSTEP…');button.clicked.connect(lambda:install_system(d));rows.insertWidget(0,button);self.buttons['Install MacaqueSTEP…']=button
  rows.addStretch();scroll.setWidget(body);v.addWidget(scroll,1);self.setContextMenuPolicy(Qt.CustomContextMenu);self.customContextMenuRequested.connect(self.context);d.area.subWindowActivated.connect(self.refresh);self.timer=QTimer(self);self.timer.setInterval(300);self.timer.timeout.connect(self.refresh);self.timer.start();self.refresh()
 def button(self,text):
  button=MenuRow(text);button.setObjectName('sideAppMenuRow');button.setAccessibleName(text.replace('  ▸',''));button.setFixedHeight(26);button.setFocusPolicy(Qt.NoFocus);return button
 def refresh(self,*_):
  if self.d.exiting:return
  w=self.backend.active();name=APP_NAMES.get(app_kind(w.property('running_key')),'Application') if w else 'MacaqueSTEP';self.title.setText(self.title.fontMetrics().elidedText(name,Qt.ElideRight,self.WIDTH-14));self.title.setToolTip(name+' — drag this title to move the menu')
  for label in ('Hide','Hide Others'):self.buttons[label].setEnabled(w is not None)
  self.buttons['Print…'].setEnabled(self.backend.printable(w))
 def populate(self,name):
  menu=self.menus[name];mapping={'Info':'MacaqueSTEP','Windows':'Window'}
  if name not in ('Tools','Services'):self.backend.populate(mapping.get(name,name),menu);return
  menu.clear()
  if name=='Tools':
   from os_integration import available,install_system
   if available():self.backend.add(menu,'Install MacaqueSTEP…',lambda:install_system(self.d));menu.addSeparator()
   for label,method in TOOLS:self.backend.add(menu,label,getattr(self.d,method))
  else:
   for label,callback in [('File Search…',self.d.search_files),('Screenshot…',self.d.screenshot),('Sound Effects…',self.d.sound_preferences),('System Controls…',self.d.system_controls),('Backups…',self.d.backups),('Preferences…',self.d.preferences)]:self.backend.add(menu,label,callback)
 def open_menu(self,name):
  self.refresh();button=self.buttons[name];self.menus[name].popup(button.mapToGlobal(QPoint(button.width(),0)))
 def hide_app(self):
  w=self.backend.active()
  if w:self.d.hide_application(w.property('running_key'))
  self.refresh()
 def hide_others(self):
  w=self.backend.active()
  if w:self.d.hide_others(w.property('running_key'))
  self.refresh()
 def print_app(self):
  w=self.backend.active()
  if w:self.backend.print_window(w)
 def context(self,pos):
  menu=QMenu(self);menu.addAction('Center this menu',self.center_menu);menu.addAction('Reset menu position',self.reset_position);menu.addSeparator();menu.addAction('Show horizontal app menus',self.d.show_classic_menus);menu.addAction('Preferences…',self.d.preferences);menu.exec(self.mapToGlobal(pos))

 def saved_position(self):
  try:
   value=json.loads(self.d.settings.value('floating_menu_position','null'))
   if isinstance(value,list) and len(value)==2 and all(type(n)==int and abs(n)<32768 for n in value):return QPoint(*value)
  except (ValueError,TypeError):pass
  return QPoint(8,80)
 def clamp_position(self,point):
  parent=self.parentWidget();return QPoint(max(0,min(point.x(),max(0,parent.width()-self.width()-2))),max(0,min(point.y(),max(0,parent.height()-self.height()-2))))
 def place(self,point,save=False):
  self.move(self.clamp_position(point));self.raise_()
  if save:self.d.settings.setValue('floating_menu_position',json.dumps([self.x(),self.y()]))
 def begin_drag(self,event):
  self.drag_offset=event.globalPosition().toPoint()-self.mapToGlobal(QPoint(0,0));self.title.setCursor(Qt.ClosedHandCursor);self.raise_()
 def drag_to(self,event):
  point=self.parentWidget().mapFromGlobal(event.globalPosition().toPoint()-self.drag_offset);self.place(point)
 def end_drag(self):
  if self.drag_offset is not None:self.drag_offset=None;self.title.setCursor(Qt.OpenHandCursor);self.place(self.pos(),True)
 def center_menu(self):self.place(QPoint((self.parentWidget().width()-self.width())//2,(self.parentWidget().height()-self.height())//2),True)
 def reset_position(self):self.place(QPoint(8,80),True)
