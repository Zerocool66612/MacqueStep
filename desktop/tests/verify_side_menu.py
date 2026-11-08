import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sandbox=tempfile.TemporaryDirectory(prefix='step-side-menu-');root=Path(sandbox.name)
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
from PySide6.QtCore import QPoint
from backup_app import create_backup,schedule_restore,apply_pending_restore
app=QApplication([]);d=Desktop();d.resize(1450,950);d.show();QTest.qWait(300);side=d.side_app_menu

def choose(name,identifier):side.populate(name);return next(a for a in side.menus[name].actions() if a.objectName()==identifier)
try:
 assert not side.isVisible() and d.area.viewportMargins().left()==0
 d.set_top_bar_visible(False);QTest.qWait(60);assert d.menu_stack.isHidden() and side.isVisible();assert d.area.viewportMargins().left()==0
 assert set(side.buttons)>={'Info','File','Edit','View','Go','Tools','Windows','Services','Help','Hide','Hide Others','Show All','Print…','Quit Preview'}
 for name in side.menus:side.populate(name);assert side.menus[name].actions()
 # The menu floats over the desktop without reserving a dock strip.
 assert d.area.viewportMargins().left()==0 and side.parentWidget() is d.area
 w=d.editor();key=w.property('running_key');d.activate_running(key,False);w.content.editor.setFocus();QTest.qWait(30);side.refresh();assert side.title.text()=='Text Editor'
 w.content.editor.setPlainText('Saved from the left menu');w.content.editor.document().setModified(True);destination=root/'left-menu.txt';saved=[]
 def save_from_popup():
  action=next(a for a in side.menus['File'].actions() if a.objectName()=='file.save');saved.append(action.isEnabled());action.trigger();side.menus['File'].close()
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(destination),'')):
  QTimer.singleShot(50,save_from_popup);QTest.mouseClick(side.buttons['File'],Qt.LeftButton);QTest.qWait(100)
 assert saved==[True] and destination.read_text()=='Saved from the left menu'
 w.content.editor.selectAll();choose('Edit','edit.copy').trigger();assert QApplication.clipboard().text()=='Saved from the left menu';choose('Edit','edit.cut').trigger();assert not w.content.editor.toPlainText();choose('Edit','edit.undo').trigger();assert w.content.editor.toPlainText()=='Saved from the left menu';w.content.editor.document().setModified(False)
 side.buttons['Hide Others'].click();assert d.windows['files'].property('app_hidden');side.buttons['Show All'].click();assert not d.windows['files'].property('app_hidden')
 # App title and disabled state follow activation, and menus remain available between workspaces.
 d.files();d.activate_running('files',False);QTest.qWait(30);side.refresh();assert side.title.text()=='File Viewer';assert not choose('File','file.save').isEnabled()
 d.switch_workspace(2);QTest.qWait(30);assert side.isVisible();d.switch_workspace(0)
 for theme in ('Classic','Light','Dark'):
  d.apply_theme(theme)
  for width,height in ((850,600),(1450,950)):
   d.resize(width,height);QTest.qWait(50);assert side.isVisible() and side.geometry().bottom()<d.area.height();assert d.area.viewportMargins().left()==0
 d.activate_running(key,False);d.maximize_running(key);QTest.qWait(30);assert side.isVisible() and d.area.viewportMargins().left()==0;d.maximize_running(key)
 # Switching back removes the reservation and never leaves two visible app menus.
 d.set_bar_style('classic');QTest.qWait(30);assert not side.isVisible() and d.menu_stack.isVisible() and d.area.viewportMargins().left()==0
 d.show_left_app_menu();d.settings.setValue('left_menu_enabled',False);d.sync_side_app_menu();assert not side.isVisible() and d.area.viewportMargins().left()==0
 d.show_left_app_menu();assert side.isVisible() and d.settings.value('left_menu_enabled',False,type=bool)
 # Preferences and backups persist the automatic left-menu choice.
 d.preferences();combo=d.findChild(QComboBox,'desktopBarStyle');assert combo.currentData()=='none';check=d.findChild(QCheckBox,'topBarVisibility');assert not check.isChecked()
 backup=root/'backup.zip';create_backup(d.store,d.settings,backup);schedule_restore(backup);restored=QSettings(str(root/'restored.ini'),QSettings.IniFormat);assert apply_pending_restore(restored);assert restored.value('left_menu_enabled',False,type=bool) and restored.value('desktop_bar_style')=='none'
 w.content.editor.document().setModified(False);d.settings.sync();d.close();QTest.qWait(60);d2=Desktop();d2.show();QTest.qWait(300);assert d2.side_app_menu.isVisible() and d2.menu_stack.isHidden();d2.close();QTest.qWait(50)
 print('PASS automatic persistent left menu, active-app title/commands, actual Save popup, clipboard/undo, hide/show, workspace/theme/size behavior, floating geometry, layout switching, preferences, backups and restart')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:
   for window in widget.windows.values():
    if hasattr(window.content,'editor'):window.content.editor.document().setModified(False)
   widget.close()
 app.processEvents()
