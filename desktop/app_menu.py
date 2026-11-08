"""Classic global app menus with explicit adapters to existing app commands."""
import weakref
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt,QTimer,QRect,QPoint
from PySide6.QtGui import QTextDocument,QPainter
from PySide6.QtWidgets import *
from shiboken6 import isValid
from running_dock import app_kind,APP_NAMES
from file_manager import FileManager
from terminal import Terminal
from paint_app import Paint
from organizer import Notes,Tasks
from archives import Archives
class AppMenu(QFrame):
 def __init__(self,d):
  super().__init__();self.d=d;self.last_focus=None;self.printer=None;self.setObjectName('classicMenuBar');self.setFixedHeight(30);row=QHBoxLayout(self);row.setContentsMargins(7,0,9,0);row.setSpacing(10);self.bar=QWidget();self.bar.setObjectName('classicMenus');buttons=QHBoxLayout(self.bar);buttons.setContentsMargins(0,0,0,0);buttons.setSpacing(0);row.addWidget(self.bar);self.menus={};self.menu_buttons={}
  for name in ('MacaqueSTEP','File','Edit','View','Go','Window','Help'):
   button=QToolButton();button.setObjectName('classicMenu'+name);button.setProperty('classicMenuButton',True);button.setText('&'+name);button.setToolButtonStyle(Qt.ToolButtonTextOnly);button.setAutoRaise(True);button.setFocusPolicy(Qt.NoFocus);button.setAccessibleName(name+' menu');button.setFixedHeight(28);button.setPopupMode(QToolButton.InstantPopup);menu=QMenu(button);menu.setTitle(name);button.setMenu(menu);buttons.addWidget(button);self.menu_buttons[name]=button;self.menus[name]=menu;menu.aboutToShow.connect(lambda n=name:self.populate(n))
  self.app_label=QLabel('Desktop');self.app_label.setStyleSheet('font-weight:bold');row.addWidget(self.app_label);row.addStretch();self.clock=QLabel();row.addWidget(self.clock);self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(1000);self.tick();QApplication.instance().focusChanged.connect(self.focus_changed);d.area.subWindowActivated.connect(self.update_title)
 def tick(self):self.clock.setText(datetime.now().strftime('%a %d %b  %H:%M'))
 def update_title(self,*_):
  w=self.active();self.app_label.setText(APP_NAMES.get(app_kind(w.property('running_key')),'Application') if w else 'Desktop')
 def active(self):
  w=self.d.area.activeSubWindow()
  return w if w and isValid(w) and w.property('running_key') in self.d.windows and w.isVisible() and not w.isMinimized() else None
 def focus_changed(self,old,new):
  if new and isValid(new):
   w=self.active()
   if w and isinstance(new,(QLineEdit,QTextEdit,QPlainTextEdit,QAbstractItemView)) and (new is w.content or w.content.isAncestorOf(new)):self.last_focus=weakref.ref(new)
 def menu_content(self,w):
  content=w.content
  if hasattr(content,'active_file_manager'):
   target=self.last_focus() if self.last_focus else None
   return content.active_file_manager(target if target and isValid(target) else None)
  return content
 def target(self,w):
  target=self.last_focus() if self.last_focus else None
  if target and isValid(target) and (target is w.content or w.content.isAncestorOf(target)):return target
  content=self.menu_content(w)
  if isinstance(content,Terminal):return content.view
  if hasattr(content,'editor'):return content.editor
  if isinstance(content,Notes):return content.body
  if isinstance(content,FileManager):return content.view
  return content.focusWidget()
 def add(self,menu,label,callback=None,enabled=True,identifier=None,w=None,checked=None):
  action=menu.addAction(label);action.setEnabled(bool(callback) and enabled)
  if identifier:action.setObjectName(identifier)
  if checked is not None:action.setCheckable(True);action.setChecked(checked)
  if callback:
   def invoke(*_):
    if w is None or (isValid(w) and self.d.windows.get(w.property('running_key')) is w):callback()
   action.triggered.connect(invoke)
  return action
 def command(self,content,name):return getattr(content,'menu_commands',{}).get(name)
 def populate(self,name,menu=None):
  menu=self.menus[name] if menu is None else menu;menu.clear();w=self.active();content=self.menu_content(w) if w else None;key=w.property('running_key') if w else None;self.update_title()
  if name=='MacaqueSTEP':
   for label,callback in [('About MacaqueSTEP…',self.d.about),('Preferences…',self.d.preferences),('Applications…',self.d.launcher),('Command Palette…',self.d.command_palette),('Desktop Sessions…',self.d.sessions_panel),('Sound Effects…',self.d.sound_preferences)]:self.add(menu,label,callback)
   menu.addSeparator();self.add(menu,'Quit MacaqueSTEP Preview',self.d.close);return
  if name=='File':
   new=menu.addMenu('New')
   for label,callback in [('Text Document',self.d.editor),('Note',self.new_note),('Task',self.new_task),('Paint Drawing',self.new_drawing)]:self.add(new,label,callback)
   if isinstance(content,FileManager):self.add(new,'Folder…',content.mkdir,w=w)
   opener=self.command(content,'open') if content else None
   if isinstance(content,FileManager):opener=lambda:content.open(content.view.currentIndex())
   elif isinstance(content,Paint):opener=content.open
   elif isinstance(content,Archives):opener=content.choose
   elif content and hasattr(content,'load_media'):opener=content.load_media
   self.add(menu,'Open…',opener or self.open_file,identifier='file.open',w=w if opener else None,enabled=not isinstance(content,FileManager) or content.view.currentIndex().isValid())
   save=self.command(content,'save') if content else None;save_as=self.command(content,'save_as') if content else None
   if isinstance(content,Paint):save=content.save;save_as=content.save
   elif isinstance(content,Notes):save=content.flush;save_as=content.export
   self.add(menu,'Save',save,identifier='file.save',w=w);self.add(menu,'Save As…' if not isinstance(content,Notes) else 'Export Note…',save_as,identifier='file.save_as',w=w)
   if isinstance(content,Archives):self.add(menu,'Extract Selected…',content.extract,enabled=content.selected() is not None,w=w)
   if isinstance(content,FileManager):self.add(menu,'Get Info…',content.properties,enabled=content.selected() is not None,w=w)
   menu.addSeparator();printable=self.printable(w)
   self.add(menu,'Page Setup…',lambda:self.page_setup(w),enabled=printable,identifier='file.page_setup',w=w);self.add(menu,'Print…',lambda:self.print_window(w),enabled=printable,identifier='file.print',w=w)
   menu.addSeparator();self.add(menu,'Close Window',w.close if w else None,identifier='file.close',w=w);return
  if name=='Edit':self.edit_menu(menu,w);return
  if name=='View':
   styles=menu.addMenu('Menu Bar Layout')
   for label,style in [('Classic App Menus','classic'),('Desktop Toolbar','toolbar'),('Floating App Menu','none')]:self.add(styles,label,lambda value=style:self.d.set_bar_style(value),checked=self.d.bar_style()==style)
   self.add(menu,'Full Screen',self.d.toggle_fullscreen,checked=self.d.isFullScreen());self.add(menu,'Workspace Overview…',self.d.overview);self.add(menu,'Show Desktop / Restore Windows',self.d.show_desktop)
   if isinstance(content,FileManager):self.add(menu,'Show Hidden Files',lambda:content.hidden.setChecked(not content.hidden.isChecked()),checked=content.hidden.isChecked(),w=w)
   if content and hasattr(content,'player'):
    for title,callback in [('Play',content.player.play),('Pause',content.player.pause),('Stop',content.player.stop)]:self.add(menu,title,callback,w=w)
   return
  if name=='Go':
   if isinstance(content,FileManager):
    self.add(menu,'Back',lambda:content.travel(-1),enabled=content.hpos>0,w=w);self.add(menu,'Forward',lambda:content.travel(1),enabled=content.hpos<len(content.history)-1,w=w);self.add(menu,'Enclosing Folder',lambda:content.navigate(Path(content.path.text()).parent),w=w);menu.addSeparator()
   for title,path in [('Home',Path.home()),('Documents',Path.home()/'Documents'),('Downloads',Path.home()/'Downloads')]:self.add(menu,title,lambda p=path:self.go_folder(p),enabled=path.is_dir())
   spaces=menu.addMenu('Workspaces')
   for n in range(4):self.add(spaces,self.d.workspace_name(n),lambda i=n:self.d.switch_workspace(i),checked=n==self.d.workspace)
   return
  if name=='Window':
   self.add(menu,'Minimize',lambda:self.d.minimize_running(key),enabled=bool(w),w=w);self.add(menu,'Zoom / Restore',lambda:self.d.maximize_running(key),enabled=bool(w),w=w);self.add(menu,'Shade / Unshade',lambda:self.d.set_shaded(key,not w.property('shaded')),enabled=bool(w),w=w)
   if w:
    self.d.pin_menu(menu,self.d.entry_for_window(key));self.add(menu,'Hide Application',lambda:self.d.hide_application(key),w=w);self.add(menu,'Hide Others',lambda:self.d.hide_others(key),w=w)
   self.add(menu,'Show All Applications',self.d.show_all_applications);menu.addSeparator();self.add(menu,'Tile Workspace',self.d.tile_workspace);self.add(menu,'Cascade Workspace',self.d.cascade_workspace);self.add(menu,'Undo Layout',self.d.undo_layout);menu.addSeparator()
   for other,window in self.d.windows.items():self.add(menu,window.windowTitle(),lambda k=other:self.d.activate_running(k,False),checked=other==key)
   return
  if name=='Help':
   self.add(menu,'MacaqueSTEP Help',self.d.help_center);self.add(menu,'Project Status',self.d.project_status);self.add(menu,'Unix Readiness Inventory',self.d.readiness_panel)
 def edit_menu(self,menu,w):
  content=self.menu_content(w) if w else None;target=self.target(w) if w else None
  text=isinstance(target,(QLineEdit,QTextEdit,QPlainTextEdit));terminal=isinstance(content,Terminal) and target is content.view
  files=isinstance(content,FileManager) and not text;paint=isinstance(content,Paint);writable=text and not target.isReadOnly();selected=(target.hasSelectedText() if isinstance(target,QLineEdit) else target.textCursor().hasSelection()) if text else False
  undo=target.isUndoAvailable() if isinstance(target,QLineEdit) else target.document().isUndoAvailable() if text else bool(content.canvas.undo_stack) if paint else False
  redo=target.isRedoAvailable() if isinstance(target,QLineEdit) else target.document().isRedoAvailable() if text else False
  self.add(menu,'Undo',content.canvas.undo if paint else target.undo if writable else None,enabled=undo,identifier='edit.undo',w=w);self.add(menu,'Redo',target.redo if writable else None,enabled=redo,identifier='edit.redo',w=w);menu.addSeparator()
  has_files=files and content.selected() is not None;mime=QApplication.clipboard().mimeData();file_paste=files and mime and mime.hasUrls()
  self.add(menu,'Cut',content.cut if files else target.cut if writable else None,enabled=has_files or (writable and selected),identifier='edit.cut',w=w)
  self.add(menu,'Copy',content.copy if files else target.copy if text else None,enabled=has_files or selected,identifier='edit.copy',w=w)
  paste=content.paste if files else (lambda:content.write(QApplication.clipboard().text().encode())) if terminal else target.paste if writable else None
  self.add(menu,'Paste',paste,enabled=bool(file_paste) or ((writable or terminal) and bool(QApplication.clipboard().text())),identifier='edit.paste',w=w)
  self.add(menu,'Delete Selection',lambda:target.del_() if isinstance(target,QLineEdit) else target.textCursor().removeSelectedText(),enabled=writable and selected,identifier='edit.delete',w=w)
  select_all=content.view.selectAll if files else target.selectAll if text else None;self.add(menu,'Select All',select_all,identifier='edit.select_all',w=w)
  if files:
   self.add(menu,'Rename…',content.rename,enabled=has_files,w=w);self.add(menu,'Move to Trash…',content.trash,enabled=has_files,w=w)
  menu.addSeparator();find=self.command(content,'find') if content else None
  if isinstance(content,Notes):find=content.search.setFocus
  elif isinstance(content,FileManager):find=content.filter.setFocus
  self.add(menu,'Find…',find,identifier='edit.find',w=w);self.add(menu,'Find Next',self.command(content,'find_next') if content else None,identifier='edit.find_next',w=w)
  if paint:self.add(menu,'Choose Color…',content.color,w=w);self.add(menu,'Clear Drawing…',content.clear,w=w)
  if isinstance(content,Notes):self.add(menu,'Delete Note…',content.delete,w=w)
  if isinstance(content,Tasks):self.add(menu,'Clear Completed Tasks',content.clear,w=w)
 def open_file(self):
  path=QFileDialog.getOpenFileName(self.d,'Open file',str(Path.home()))[0]
  if path:self.d.open_path(Path(path))
 def new_note(self):
  existed='notes' in self.d.windows;self.d.notes()
  if existed:self.d.windows['notes'].content.new()
 def new_task(self):self.d.tasks();self.d.windows['tasks'].content.entry.setFocus()
 def new_drawing(self):
  existed='paint' in self.d.windows;self.d.paint_app()
  if existed:self.d.windows['paint'].content.clear()
 def go_folder(self,path):
  window=self.active();content=self.menu_content(window) if window else None
  if isinstance(content,FileManager):content.navigate(path)
  else:self.d.files();self.d.windows['files'].content.navigate(path)
 def print_target(self,w):
  if not w:return None
  c=w.content
  if hasattr(c,'editor'):return c.editor
  if isinstance(c,Terminal):return c.view
  if isinstance(c,(QTextEdit,QPlainTextEdit)):return c
  return c.findChild(QTextEdit) or c.findChild(QPlainTextEdit)
 def printable(self,w):
  return bool(w) and (isinstance(w.content,(Paint,Notes)) or self.print_target(w) is not None)
 def get_printer(self):
  from PySide6.QtPrintSupport import QPrinter
  if self.printer is None:self.printer=QPrinter(QPrinter.HighResolution)
  return self.printer
 def page_setup(self,w):
  if not self.printable(w):return
  from PySide6.QtPrintSupport import QPageSetupDialog
  QPageSetupDialog(self.get_printer(),self.d).exec()
 def print_window(self,w):
  if not self.printable(w):return
  from PySide6.QtPrintSupport import QPrintDialog
  printer=self.get_printer()
  if QPrintDialog(printer,self.d).exec()!=QDialog.Accepted:return
  try:self.render_print(w,printer)
  except OSError as error:QMessageBox.warning(self.d,'Print failed',str(error))
 def render_print(self,w,printer):
  c=w.content
  if isinstance(c,Paint):
   painter=QPainter(printer)
   if not painter.isActive():raise OSError('Could not start the printer.')
   try:
    rect=painter.viewport();size=c.canvas.image.size();size.scale(rect.size(),Qt.KeepAspectRatio);painter.setRenderHint(QPainter.SmoothPixmapTransform,True);painter.drawImage(QRect(QPoint(0,0),size),c.canvas.image)
   finally:painter.end()
  elif isinstance(c,Notes):
   document=QTextDocument();document.setPlainText(c.title.text()+'\n\n'+c.body.toPlainText());document.print_(printer)
  else:self.print_target(w).document().print_(printer)
