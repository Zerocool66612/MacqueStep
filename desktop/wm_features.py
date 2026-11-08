import json
from PySide6.QtCore import Qt,QEvent,QObject,QTimer,QRect
from PySide6.QtWidgets import *
from running_dock import app_kind,APP_NAMES
from shiboken6 import isValid
class FocusEvents(QObject):
 def __init__(self,desktop):super().__init__(desktop);self.desktop=desktop
 def eventFilter(self,obj,event):
  d=self.desktop
  if not isValid(d) or d.exiting or event.type()!=QEvent.Enter or not isinstance(obj,QWidget):return False
  if not d.settings.value('wm_focus_follows_mouse',False,type=bool) or QApplication.activePopupWidget() or QApplication.activeModalWidget():return False
  window=obj
  while window is not None and not isinstance(window,QMdiSubWindow):window=window.parentWidget()
  if window is not None and window.isVisible() and not window.isMinimized():
   d.area.setActiveSubWindow(window)
   if d.settings.value('wm_raise_on_focus',False,type=bool):window.raise_();d.enforce_stacking()
  return False
class WindowRules(QWidget):
 def __init__(self,desktop):
  super().__init__();self.desktop=desktop;v=QVBoxLayout(self);form=QFormLayout();v.addLayout(form);self.app=QComboBox()
  for key,title in sorted(APP_NAMES.items(),key=lambda pair:pair[1]):self.app.addItem(title,key)
  self.workspace=QComboBox();self.workspace.addItem('Current workspace',-1)
  for i in range(4):self.workspace.addItem(desktop.workspace_name(i),i)
  self.sticky=QCheckBox('Show on all workspaces');self.above=QCheckBox('Keep above other windows');self.shaded=QCheckBox('Start shaded');form.addRow('Application',self.app);form.addRow('Start on',self.workspace);form.addRow(self.sticky);form.addRow(self.above);form.addRow(self.shaded)
  for title,fn in [('Save rule',self.save),('Save and apply to open windows',self.apply),('Remove this rule',self.remove)]:button=QPushButton(title);button.clicked.connect(fn);v.addWidget(button)
  self.status=QLabel('Rules apply to internal MacaqueSTEP windows.');self.status.setWordWrap(True);v.addWidget(self.status);v.addStretch();self.app.currentIndexChanged.connect(self.load);self.load()
 def load(self):
  rule=self.desktop.window_rules().get(self.app.currentData(),{});self.workspace.setCurrentIndex(max(0,self.workspace.findData(rule.get('workspace',-1))));self.sticky.setChecked(bool(rule.get('sticky',False)));self.above.setChecked(bool(rule.get('above',False)));self.shaded.setChecked(bool(rule.get('shaded',False)))
 def save(self):
  rules=self.desktop.window_rules();rules[self.app.currentData()]={'workspace':self.workspace.currentData(),'sticky':self.sticky.isChecked(),'above':self.above.isChecked(),'shaded':self.shaded.isChecked()};self.desktop.settings.setValue('wm_rules',json.dumps(rules));self.status.setText('Saved. The rule applies to newly opened windows.')
 def apply(self):
  self.save()
  for key,w in list(self.desktop.windows.items()):
   if app_kind(key)==self.app.currentData():self.desktop.apply_window_rule(key,w)
  self.desktop.switch_workspace(self.desktop.workspace);self.status.setText('Applied to matching open windows.')
 def remove(self):
  rules=self.desktop.window_rules();rules.pop(self.app.currentData(),None);self.desktop.settings.setValue('wm_rules',json.dumps(rules));self.load();self.status.setText('Rule removed. Existing window state is unchanged.')
class WMFeatures:
 def workspace_names(self):
  try:names=json.loads(self.settings.value('wm_workspace_names','[]'))
  except (ValueError,TypeError):names=[]
  return [str(names[i])[:24] if i<len(names) and isinstance(names[i],str) and names[i].strip() else f'Workspace {i+1}' for i in range(4)] if isinstance(names,list) else [f'Workspace {i+1}' for i in range(4)]
 def workspace_name(self,n):return self.workspace_names()[n]
 def rename_workspace(self,n):
  name,ok=QInputDialog.getText(self,'Rename workspace','Name',text=self.workspace_name(n))
  if ok and name.strip():
   names=self.workspace_names();names[n]=name.strip()[:24];self.settings.setValue('wm_workspace_names',json.dumps(names));self.refresh_workspace_names()
 def refresh_workspace_names(self):
  for i,button in enumerate(self.workspace_buttons):button.setText(str(i+1));button.setToolTip(self.workspace_name(i));button.setAccessibleName(self.workspace_name(i))
  self.update_tasks()
  if hasattr(self,'clip'):self.clip.refresh()
 def toggle_sticky(self,key):
  if key not in self.windows:return
  w=self.windows[key];w.setProperty('sticky',not bool(w.property('sticky')));self.switch_workspace(self.workspace);self.queue_running_refresh()
 def toggle_above(self,key):
  if key not in self.windows:return
  w=self.windows[key];w.setProperty('keep_above',not bool(w.property('keep_above')));self.enforce_stacking();self.queue_running_refresh()
 def enforce_stacking(self,*_):
  if self.exiting or getattr(self,'_restacking',False):return
  self._restacking=True
  for w in self.windows.values():
   if w.property('keep_above') and w.isVisible() and not w.isMinimized():w.raise_()
  self.position_running_dock();self._restacking=False
 def set_shaded(self,key,value):
  if key not in self.windows:return
  w=self.windows[key]
  if bool(w.property('shaded'))==bool(value):return
  if value:
   if w.isMinimized():self.reopen(key)
   rect=w.property('normal_rect') if w.isMaximized() else w.geometry()
   w._shade_size=rect.size() if isinstance(rect,QRect) and rect.isValid() else w.size();w._shade_min=w.minimumSize();w._shade_max=w.maximumSize();w.showNormal();w.content.hide()
   for grip in w.widget().findChildren(QSizeGrip):grip.hide()
   w.setMinimumHeight(38);w.setMaximumHeight(38);w.resize(w.width(),38);w.setProperty('shaded',True)
  else:
   w.setMaximumSize(w._shade_max);w.setMinimumSize(w._shade_min);w.content.show()
   for grip in w.widget().findChildren(QSizeGrip):grip.show()
   w.resize(w._shade_size);w.setProperty('shaded',False);self.ensure_visible(w)
  self.queue_running_refresh()
 def window_rules(self):
  try:rules=json.loads(self.settings.value('wm_rules','{}'));return rules if isinstance(rules,dict) else {}
  except (TypeError,ValueError):return {}
 def apply_window_rule(self,key,w):
  rule=self.window_rules().get(app_kind(key))
  if not isinstance(rule,dict):return
  n=rule.get('workspace',-1)
  if type(n)==int and 0<=n<4:w.setProperty('workspace',n)
  w.setProperty('sticky',bool(rule.get('sticky',False)));w.setProperty('keep_above',bool(rule.get('above',False)));self.set_shaded(key,bool(rule.get('shaded',False)))
  if (w.property('workspace') or 0)!=self.workspace and not w.property('sticky'):w.hide()
  self.enforce_stacking()
 def rules_panel(self):
  if 'window-rules' in self.windows:self.reopen('window-rules');return
  self.window('window-rules','Application Window Rules',WindowRules(self),(140,80,550,470))
 def wm_actions(self,menu,key):
  if key not in self.windows:return
  entry=self.entry_for_window(key)
  if entry:self.pin_menu(menu,entry)
  w=self.windows[key];menu.addSeparator();menu.addAction('Unshade window' if w.property('shaded') else 'Shade to title bar',lambda:self.set_shaded(key,not bool(w.property('shaded'))))
  menu.addAction('Show application',lambda:self.unhide_application(key));menu.addAction('Show application here',lambda:self.unhide_application(key,True));menu.addAction('Hide application',lambda:self.hide_application(key));menu.addAction('Hide other applications',lambda:self.hide_others(key));menu.addAction('Show all applications',self.show_all_applications)
  sticky=menu.addAction('Show on all workspaces');sticky.setCheckable(True);sticky.setChecked(bool(w.property('sticky')));sticky.triggered.connect(lambda:self.toggle_sticky(key));above=menu.addAction('Keep above other windows');above.setCheckable(True);above.setChecked(bool(w.property('keep_above')));above.triggered.connect(lambda:self.toggle_above(key));menu.addAction('Application window rules…',self.rules_panel)
