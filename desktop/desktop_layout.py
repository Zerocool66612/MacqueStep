"""Optional top bar and desktop menus for the traditional layout."""
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QMenu,QCheckBox
from command_center import TOOLS
from drawers import load_drawers,launch_entry
class DesktopLayout:
 def setup_app_menu(self):
  from app_menu import AppMenu
  from PySide6.QtWidgets import QStackedWidget,QSizePolicy
  layout=self.centralWidget().layout();self.desktop_toolbar=layout.takeAt(0).widget();self.menu_stack=QStackedWidget();self.menu_stack.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed);self.menu_stack.addWidget(self.desktop_toolbar);self.app_menu=AppMenu(self);self.menu_stack.addWidget(self.app_menu);layout.insertWidget(0,self.menu_stack)
  from side_app_menu import SideAppMenu
  self.side_app_menu=SideAppMenu(self);self.set_bar_style(self.bar_style())
 def bar_style(self):
  value=self.settings.value('desktop_bar_style','classic')
  return value if value in ('classic','toolbar','none') else 'classic'
 def top_bar_visible(self):return self.bar_style()!='none'
 def set_bar_style(self,style):
  if style not in ('classic','toolbar','none'):return
  self.settings.setValue('desktop_bar_style',style);self.settings.setValue('top_bar_visible',style!='none')
  if style!='none':self.settings.setValue('desktop_bar_last',style)
  if hasattr(self,'menu_stack'):
   self.menu_stack.setCurrentWidget(self.desktop_toolbar if style=='toolbar' else self.app_menu);self.menu_stack.setFixedHeight(max(40,self.desktop_toolbar.sizeHint().height()) if style=='toolbar' else 30);self.menu_stack.setVisible(style!='none')
  checkbox=self.findChild(QCheckBox,'topBarVisibility')
  if checkbox:checkbox.blockSignals(True);checkbox.setChecked(style!='none');checkbox.blockSignals(False)
  from PySide6.QtWidgets import QComboBox
  combo=self.findChild(QComboBox,'desktopBarStyle')
  if combo:combo.blockSignals(True);combo.setCurrentIndex(max(0,combo.findData(style)));combo.blockSignals(False)
  if hasattr(self,'side_app_menu'):self.sync_side_app_menu()
  QTimer.singleShot(0,self.update_desktop_layout)
 def set_top_bar_visible(self,visible):
  last=self.settings.value('desktop_bar_last','classic')
  self.set_bar_style(last if visible and last in ('classic','toolbar') else 'classic' if visible else 'none')
 def show_classic_menus(self):
  self.set_bar_style('classic')
  if hasattr(self,'app_menu'):
   self.menu_stack.show();self.app_menu.show();self.app_menu.bar.show()
   for button in self.app_menu.menu_buttons.values():button.show()
 def show_left_app_menu(self):
  self.settings.setValue('left_menu_enabled',True);self.set_bar_style('none');self.sync_side_app_menu()
 def sync_side_app_menu(self):
  if not hasattr(self,'side_app_menu'):return
  visible=self.bar_style()=='none' and self.settings.value('left_menu_enabled',True,type=bool)
  if self.area.viewportMargins().left()!=0:self.area.setViewportMargins(0,0,0,0)
  self.side_app_menu.setVisible(visible);self.update_side_menu_geometry();self.side_app_menu.refresh()
 def update_side_menu_geometry(self):
  if self.exiting or not hasattr(self,'side_app_menu'):return
  height=max(0,self.area.height()-4)
  if self.area.horizontalScrollBar().isVisible():height-=self.area.horizontalScrollBar().height()
  self.side_app_menu.resize(self.side_app_menu.WIDTH,max(0,min(height,self.side_app_menu.title.height()+6+sum(b.height() for b in self.side_app_menu.buttons.values()))))
  if self.side_app_menu.drag_offset is None:self.side_app_menu.place(self.side_app_menu.saved_position())
  if self.side_app_menu.isVisible():self.side_app_menu.raise_()
 def toggle_top_bar(self):self.set_top_bar_visible(not self.top_bar_visible())
 def update_desktop_layout(self):
  if self.exiting:return
  self.sync_side_app_menu();self.fit_side_dock();self.clip.refresh();self.position_running_dock()
  for w in self.windows.values():
   if not w.isMinimized() and not w.isMaximized() and not w.property('shaded'):self.ensure_visible(w)
 def desktop_context_menu(self):
  menu=QMenu(self)
  from os_integration import available,install_system
  if available():menu.addAction('Install MacaqueSTEP…',lambda:install_system(self));menu.addSeparator()
  menu.addAction('Show File / Edit Menus',self.show_classic_menus);menu.addAction('Show floating app menu',self.show_left_app_menu);applications=menu.addMenu('Applications')
  for title,method in TOOLS:applications.addAction(title,getattr(self,method))
  menu.addAction('Terminal',self.terminal);menu.addAction('Preferences…',self.preferences);menu.addAction('Command palette…',self.command_palette)
  workspaces=menu.addMenu('Workspaces')
  for n in range(4):
   action=workspaces.addAction(self.workspace_name(n),lambda checked=False,i=n:self.switch_workspace(i));action.setCheckable(True);action.setChecked(n==self.workspace)
  workspaces.addSeparator();workspaces.addAction('Rename current workspace…',lambda:self.rename_workspace(self.workspace));workspaces.addAction('Workspace overview…',self.overview)
  windows=menu.addMenu('Windows')
  for key,w in self.windows.items():windows.addAction(w.windowTitle(),lambda checked=False,k=key:self.activate_running(k,False))
  windows.addSeparator();windows.addAction('Open Windows…',self.window_list);windows.addAction('Show all applications',self.show_all_applications);windows.addAction('Show desktop / restore windows',self.show_desktop)
  drawers=menu.addMenu('Drawers')
  for drawer in load_drawers(self.settings):
   sub=drawers.addMenu(drawer['name'])
   for entry in drawer['entries']:sub.addAction(entry['name'],lambda checked=False,e=entry:launch_entry(self,e))
  drawers.addSeparator();drawers.addAction('Drawer Shelf…',self.drawer_shelf);drawers.addAction('Customize drawers…',self.open_drawers)
  menu.addSeparator();action=menu.addAction('Show top bar');action.setObjectName('toggleTopBar');action.setCheckable(True);action.setChecked(self.top_bar_visible());action.toggled.connect(self.set_top_bar_visible);action.setToolTip('Ctrl+Alt+B also toggles the top bar.');layouts=menu.addMenu('Menu Bar Layout')
  for title,style in [('Classic App Menus','classic'),('Desktop Toolbar','toolbar'),('Left App Menu','none')]:
   choice=layouts.addAction(title,lambda checked=False,value=style:self.set_bar_style(value));choice.setCheckable(True);choice.setChecked(self.bar_style()==style)
  menu.addAction('Restore core window layout',self.reset_layout);menu.addSeparator();menu.addAction('Exit preview',self.close)
  return menu
 def desktop_menu(self,pos):self.desktop_context_menu().exec(self.area.mapToGlobal(pos))
