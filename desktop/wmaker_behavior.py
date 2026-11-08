"""Window Maker-inspired behavior for internal windows, not an external WM."""
from PySide6.QtCore import Qt,QRect,QEvent,QObject
from PySide6.QtWidgets import QApplication
from running_dock import app_kind
class TitleEvents(QObject):
 def __init__(self,d):super().__init__(d);self.d=d
 def eventFilter(self,obj,event):
  if self.d.exiting:return False
  if event.type()==QEvent.Wheel:
   key=obj.property('wm_title_key')
   if key in self.d.windows:
    if event.angleDelta().y():self.d.set_shaded(key,event.angleDelta().y()>0);event.accept();return True
  return False
class WMBehavior:
 def hide_application(self,key):
  if key not in self.windows:return
  kind=app_kind(key)
  for other,w in self.windows.items():
   if app_kind(other)==kind:w.setProperty('app_hidden',True);w.hide()
  self.queue_running_refresh()
 def unhide_application(self,key,here=False):
  if key not in self.windows:return
  kind=app_kind(key)
  for other,w in self.windows.items():
   if app_kind(other)==kind:
    w.setProperty('app_hidden',False)
    if here:w.setProperty('workspace',self.workspace)
  self.switch_workspace(self.workspace)
 def hide_others(self,key):
  if key not in self.windows:return
  kind=app_kind(key)
  for other,w in self.windows.items():
   if app_kind(other)!=kind and w.isVisible():w.setProperty('app_hidden',True);w.hide()
  self.queue_running_refresh()
 def show_all_applications(self):
  for w in self.windows.values():w.setProperty('app_hidden',False)
  self.switch_workspace(self.workspace)
 def unhide_entry(self,entry):
  from dock_workspace import ACTION
  matches=[key for key in self.windows if ACTION.get(app_kind(key))==entry.get('action')]
  if matches and any(self.windows[key].property('app_hidden') for key in matches):self.unhide_application(matches[0]);self.activate_running(matches[0],False);return True
  return False
 def titlebar_double_click(self,key,event):
  if key not in self.windows:return
  mods=event.modifiers();w=self.windows[key]
  if mods & (Qt.ControlModifier|Qt.ShiftModifier):
   previous=w.property('wm_axis_rect')
   if isinstance(previous,QRect):w.setGeometry(previous);w.setProperty('wm_axis_rect',None);self.ensure_visible(w);return
   self.set_shaded(key,False);w.showNormal();original=QRect(w.geometry());rect=QRect(original);available=self.work_rect();w.setProperty('wm_axis_rect',original)
   if mods & Qt.ControlModifier:rect.setY(0);rect.setHeight(available.height())
   if mods & Qt.ShiftModifier:rect.setX(0);rect.setWidth(available.width())
   w.setGeometry(rect);return
  if self.settings.value('wm_double_click','Shade')=='Shade':self.set_shaded(key,not bool(w.property('shaded')))
  else:self.maximize_running(key)
