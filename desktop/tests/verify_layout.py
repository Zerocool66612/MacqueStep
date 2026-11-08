import os,sys,tempfile
from pathlib import Path
sandbox=tempfile.TemporaryDirectory(prefix='step-layout-');root=Path(sandbox.name)
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
from backup_app import create_backup,schedule_restore,apply_pending_restore
app=QApplication([]);d=Desktop();d.resize(1450,950);d.show();QTest.qWait(300)
try:
 bar=d.centralWidget().layout().itemAt(0).widget();before=d.area.viewport().height();assert bar.isVisible()
 d.preferences();check=d.findChild(QCheckBox,'topBarVisibility');check.setChecked(False);QTest.qWait(60);assert bar.isHidden() and not d.top_bar_visible();assert d.area.viewport().height()>before
 menu=d.desktop_context_menu();assert {a.text() for a in menu.actions()}>={'Applications','Workspaces','Windows','Drawers','Preferences…'}
 action=next(a for a in menu.actions() if a.objectName()=='toggleTopBar');assert not action.isChecked();action.trigger();QTest.qWait(40);assert bar.isVisible() and check.isChecked()
 # A desktop-level shortcut restores access when the bar is hidden.
 d.set_top_bar_visible(False);d.windows['preferences'].content.setFocus();QTest.qWait(30);QTest.keyClick(d,Qt.Key_B,Qt.ControlModifier|Qt.AltModifier);QTest.qWait(40);assert bar.isVisible()
 assert all(button.isVisible() for button in d.side_widgets) and d.clip.isVisible()
 d.set_top_bar_visible(False);backup=root/'backup.zip';create_backup(d.store,d.settings,backup);schedule_restore(backup);restored=QSettings(str(root/'restored.ini'),QSettings.IniFormat);assert apply_pending_restore(restored) and restored.value('top_bar_visible',True,type=bool) is False
 d.settings.sync();d.close();QTest.qWait(60);d2=Desktop();d2.show();QTest.qWait(300);assert d2.centralWidget().layout().itemAt(0).widget().isHidden();assert d2.clip.isVisible() and d2.dock_scroll.isVisible();d2.toggle_top_bar();QTest.qWait(30);assert d2.centralWidget().layout().itemAt(0).widget().isVisible();d2.close();QTest.qWait(60)
 print('PASS top bar hide/show, expanded workspace, traditional menus, checkbox sync, keyboard recovery, docks/Clip, backup and restart persistence, shutdown')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:widget.close()
 app.processEvents()
