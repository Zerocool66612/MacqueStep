import os,sys,tempfile,json,subprocess
from pathlib import Path
sandbox=tempfile.TemporaryDirectory(prefix='step-menu-recovery-');root=Path(sandbox.name)
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
app=QApplication([]);d=Desktop();d.show();QTest.qWait(300)
try:
 assert not d.app_menu.findChildren(QMenuBar)
 assert list(d.app_menu.menu_buttons)==['MacaqueSTEP','File','Edit','View','Go','Window','Help']
 for width in (850,1450):
  d.resize(width,800)
  for theme in ('Classic','Light','Dark'):
   d.apply_theme(theme);d.show_classic_menus();QTest.qWait(30)
   for name,button in d.app_menu.menu_buttons.items():
    assert button.isVisible() and button.width()>10 and button.height()>10
    assert button.mapTo(d.app_menu,button.rect().topRight()).x()<d.app_menu.width(),(theme,width,name)
 # Real menu button activation must preserve the active document and its Save command.
 editor=d.editor();d.activate_running(editor.property('running_key'),False);editor.content.editor.setFocus();QTest.qWait(20);enabled=[]
 file_menu=d.app_menu.menus['File']
 def check_save():
  enabled.append(any(a.objectName()=='file.save' and a.isEnabled() for a in file_menu.actions()));file_menu.close()
 QTimer.singleShot(50,check_save);QTest.mouseClick(d.app_menu.menu_buttons['File'],Qt.LeftButton);QTest.qWait(80);assert enabled==[True]
 # Open an actual visible menu through its button, then close it without triggering a command.
 entered=[];menu=d.app_menu.menus['File'];menu.aboutToShow.connect(lambda:entered.append(True));QTimer.singleShot(50,menu.close);QTest.mouseClick(d.app_menu.menu_buttons['File'],Qt.LeftButton);QTest.qWait(80);assert entered
 d.set_bar_style('none');d.preferences();d.findChild(QPushButton,'restoreClassicMenus').click();QTest.qWait(30);assert d.bar_style()=='classic' and d.app_menu.menu_buttons['File'].isVisible()
 d.set_bar_style('none');QTest.keyClick(d,Qt.Key_M,Qt.ControlModifier|Qt.AltModifier);QTest.qWait(30);assert d.bar_style()=='classic'
 d.set_bar_style('none');menu=d.desktop_context_menu();next(a for a in menu.actions() if a.text()=='Show File / Edit Menus').trigger();assert d.bar_style()=='classic'
 # Force command repairs saved hidden/toolbar state without changing the dock side.
 d.set_bar_style('none');d.settings.setValue('dock_side','Left');d.settings.sync();d.close();QTest.qWait(60)
 desktop=Path(__file__).resolve().parents[1]/'desktop.py'
 assert subprocess.check_output([sys.executable,str(desktop),'--version'],text=True).strip()=='MacaqueSTEP 0.23'
 subprocess.run([sys.executable,str(desktop),'--classic-menus','--smoke-test'],check=True,timeout=20)
 settings=QSettings('MacaqueSTEP','DesktopPreview');settings.sync();assert settings.value('desktop_bar_style')=='classic' and settings.value('dock_side')=='Left'
 report=json.loads(subprocess.check_output([sys.executable,str(desktop),'--diagnose'],text=True));assert report['version']=='0.23' and report['menu_layout']=='classic' and report['menu_implementation']=='embedded tool buttons'
 print('PASS embedded menu visibility across themes/sizes, actual menu popup, Preferences/desktop/hotkey recovery, forced CLI recovery, version and diagnostics, preserved dock settings')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:widget.close()
 app.processEvents()
