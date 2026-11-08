import os,sys,tempfile,json,subprocess,runpy,builtins,types,errno
from pathlib import Path
from unittest.mock import patch
root=Path(tempfile.mkdtemp());os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config');os.environ['XDG_STATE_HOME']=str(root/'state');kit=Path(__file__).resolve().parents[1];sys.path.insert(0,str(kit/'desktop'))
from desktop import *
from PySide6.QtTest import QTest
from PySide6.QtCore import QPoint,QPointF,QProcess
from PySide6.QtGui import QMouseEvent
import installer_center as installer
app=QApplication([]);d=Desktop();d.resize(1400,950);d.show();QTest.qWait(200)
try:
 assert not d.settings.value('dock_fit',True,type=bool)
 assert all(d.side_grid.getItemPosition(d.side_grid.indexOf(b))[1]==0 for b in d.side_widgets)
 assert d.dock_scroll.verticalScrollBarPolicy()==Qt.ScrollBarAsNeeded
 d.show_left_app_menu();side=d.side_app_menu;QTest.qWait(50);assert d.area.viewportMargins().left()==0
 start=side.title.mapToGlobal(QPoint(30,12));target=d.area.mapToGlobal(QPoint(450,160))
 press=QMouseEvent(QEvent.MouseButtonPress,QPointF(30,12),QPointF(start),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(side.title,press)
 move=QMouseEvent(QEvent.MouseMove,QPointF(30,12),QPointF(target),Qt.NoButton,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(side.title,move)
 release=QMouseEvent(QEvent.MouseButtonRelease,QPointF(30,12),QPointF(target),Qt.LeftButton,Qt.NoButton,Qt.NoModifier);QApplication.sendEvent(side.title,release)
 assert side.x()>300 and side.y()>80;position=side.pos();d.update_desktop_layout();assert side.pos()==position
 d.resize(850,600);QTest.qWait(60);assert side.geometry().right()<d.area.width() and side.geometry().bottom()<d.area.height();d.resize(1400,950);QTest.qWait(60);assert side.pos()==position
 d.preferences();assert d.findChild(QComboBox,'desktopBarStyle').currentData()=='none'
 d.settings.setValue('dock_fit',True);d.refresh_docks();QTest.qWait(30);assert any(d.side_grid.getItemPosition(d.side_grid.indexOf(b))[1]>0 for b in d.side_widgets)
 d.settings.setValue('dock_fit',False);d.refresh_docks();d.settings.sync();d.grab().save('/tmp/step022-floating-menu.png');d.close();QTest.qWait(60)
 d2=Desktop();d2.show();QTest.qWait(160);assert d2.side_app_menu.pos()==position;assert not d2.settings.value('dock_fit',True,type=bool);d2.close();QTest.qWait(40)
finally:
 for widget in app.topLevelWidgets():
  if isinstance(widget,Desktop) and not widget.exiting:widget.close()
# The live menu has a direct installer entry; fullscreen is suspended for native UI.
import os_integration
with patch.object(os_integration,'available',return_value=True),patch.object(os_integration,'installer_center_open',return_value=False):
 d3=Desktop();d3.showFullScreen();QTest.qWait(350);assert 'Install MacaqueSTEP…' in d3.side_app_menu.buttons
 with patch.object(QProcess,'start'):
  os_integration.install_system(d3);assert not d3.isFullScreen();d3._installer_center_process.finished.emit(0,QProcess.NormalExit);QTest.qWait(100);assert d3.isFullScreen()
 d3.close();QTest.qWait(50);assert d3.exiting
# Visible installer center surfaces failures instead of detaching/masking them.
checks={'live_session':True,'source_image':'/fake/live/filesystem.squashfs','display':':99','calamares':'/usr/bin/calamares','root_helper':True,'settings':True,'sudo':'/usr/bin/sudo','pkexec':'/usr/bin/pkexec'}
with patch.object(installer,'preflight',return_value=(checks,[])),patch.object(installer,'installer_command',return_value=[sys.executable,'-c',"print('simulated installer error');raise SystemExit(7)"]),patch.object(installer.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stderr='')):
 center=installer.InstallerCenter();center.show();center.launch()
 for _ in range(100):
  QTest.qWait(20)
  if not center.running:break
 assert not center.running;assert 'code 7' in center.status.text();assert 'simulated installer error' in center.output.toPlainText();assert 'exit code: 7' in center.log.read_text();assert not center.access_granted;center.close()
with patch.object(installer,'preflight',return_value=(checks,['Missing live image'])):
 center=installer.InstallerCenter();assert not center.start.isEnabled() and 'Missing live image' in center.status.text();center.close()
# Exercise the privileged helper entirely inside a fake filesystem.
module=runpy.run_path(str(kit/'config/includes.chroot/usr/lib/macaquestep/installer-root'));g=module['run'].__globals__;fake=root/'system'
for relative in ['proc','run','etc/calamares/modules','usr/bin','run/live/medium/live']:(fake/relative).mkdir(parents=True,exist_ok=True)
(fake/'proc/cmdline').write_text('boot=live components');(fake/'run/live/medium/live/filesystem.squashfs').write_bytes(b'fixture');(fake/'etc/calamares/settings.conf').write_text('branding: macaquestep\n');(fake/'etc/calamares/modules/unpackfs.conf').write_text('unpack:\n - source: /old/image\n   sourcefs: squashfs\n   destination: ""\n');(fake/'usr/bin/calamares').write_text('fixture');(fake/'etc/fstab').write_text('original live fstab\n')
def path(value):
 value=Path(value)
 return value if value.is_relative_to(fake) else fake/str(value).lstrip('/')
real_open=builtins.open;real_mkstemp=tempfile.mkstemp
def opened(value,*args,**kwargs):return real_open(str(fake/str(value).lstrip('/')) if str(value).startswith('/run/') else value,*args,**kwargs)
g['Path']=path
with patch.object(g['os'],'geteuid',return_value=0),patch('builtins.open',side_effect=opened),patch.object(g['tempfile'],'mkstemp',side_effect=lambda **kwargs:real_mkstemp(prefix=kwargs.get('prefix','tmp'),dir=fake/'run')),patch.object(g['subprocess'],'run',return_value=types.SimpleNamespace(returncode=9)),patch.object(g['shutil'].os,'rename',side_effect=OSError(errno.EXDEV,'cross-device fixture')):
 assert module['run']()==9
assert (fake/'etc/fstab').read_text()=='original live fstab\n'
with patch.object(g['os'],'geteuid',return_value=1):
 try:module['run']();raise AssertionError('unguarded root helper')
 except RuntimeError:pass
(fake/'proc/cmdline').write_text('quiet')
try:module['live_source']();raise AssertionError('installer accepted installed session')
except RuntimeError:pass
print('PASS single-column default/migration/optional wrap, actual header drag, saved floating position/clamping/restart, visible installer exit/log/preflight, root helper live guard and fstab restoration')
