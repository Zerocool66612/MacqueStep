import os,tempfile,sys
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen'
tmp=tempfile.TemporaryDirectory();os.environ['XDG_CONFIG_HOME']=tmp.name+'/config';os.environ['XDG_DATA_HOME']=tmp.name+'/data'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from desktop import Desktop
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtCore import QProcess
app=QApplication([])
with patch('network_app.shutil.which',return_value=None):
 d=Desktop();d.network_settings();panel=d.windows['network'].content
 assert 'nmcli is unavailable' in panel.output.toPlainText()
 buttons={b.text():b for b in panel.findChildren(QPushButton)}
 assert not buttons['Connect to Wi-Fi…'].isEnabled()
 assert 'Applications…' in d.side_app_menu.buttons
 assert 'Wi-Fi & Network…' in d.side_app_menu.buttons
with patch('network_app.shutil.which',side_effect=lambda p:'/usr/bin/'+p),patch.object(QProcess,'startDetached',return_value=(True,123)) as launch:
 d.showFullScreen();panel.launch('xterm',['-T','Wi-Fi & Network','-e','nmtui-connect'])
 assert not d.isFullScreen();launch.assert_called_once_with('/usr/bin/xterm',['-T','Wi-Fi & Network','-e','nmtui-connect'])
d.launcher();old=d.windows['launcher'];button=next(b for b in old.content.findChildren(QPushButton) if b.text()=='Refresh applications');button.click();assert 'launcher' in d.windows
assert d.windows['launcher'] is old
d.close();print('PASS visible network access, unavailable-tool handling, native launch, applications refresh')
