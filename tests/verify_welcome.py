import os,sys,tempfile,json
from pathlib import Path
root=Path(tempfile.mkdtemp());os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_STATE_HOME']=str(root/'state');os.environ['XDG_CONFIG_HOME']=str(root/'config');sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from first_welcome import *
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton
app=QApplication([]);marker=root/'installed';cmdline=root/'cmdline';cmdline.write_text('quiet');assert installation_token(marker,cmdline) is None
marker.write_text('install-one');token=installation_token(marker,cmdline);cmdline.write_text('boot=live components');assert installation_token(marker,cmdline) is None;cmdline.write_text('quiet');assert claim_first_login(token,state_directory());assert (state_directory()/'setup-pending').read_text()==token;assert not claim_first_login(token,state_directory());assert claim_first_login('new-install',state_directory())
w=Welcome();w.resize(1280,720);w.show();QTest.qWait(30)
assert not w.findChildren(QPushButton) and not hasattr(w,'skip');assert w.music.source().toLocalFile().endswith('welcome.wav')
for key in (Qt.Key_Escape,Qt.Key_Return,Qt.Key_Enter,Qt.Key_Space):QTest.keyClick(w,key);assert w.isVisible()
w.close();assert w.isVisible();assert not w.completed
for ms in (2500,8000,14000):w.position=ms;w.repaint();assert not w.grab().isNull()
w.position=8000;w.grab().save('/tmp/step020-welcome.png');w.elapsed=type('FinishedClock',(),{'elapsed':lambda self:DURATION})();w.tick();assert not w.isVisible() and not w.timer.isActive()
QSettings('MacaqueSTEP','DesktopPreview').setValue('reduce_motion',True);w=Welcome();assert w.reduce_motion;w.show();w.completed=True;w.close()
print('PASS no skip/mute/buttons, ignored Escape/Enter/Space/close, original music, full-duration completion, reduced-motion still, first-installed-login gating and setup receipt')
