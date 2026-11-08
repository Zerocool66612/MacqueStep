import os,tempfile,sys
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen'
tmp=tempfile.TemporaryDirectory();os.environ['XDG_CONFIG_HOME']=tmp.name+'/config';os.environ['XDG_DATA_HOME']=tmp.name+'/data'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
import desktop,host_apps
from PySide6.QtWidgets import QApplication,QListWidget
app=QApplication([])
with patch.object(desktop,'application_entries',return_value=[{'name':'Firefox ESR','path':'/usr/share/applications/firefox-esr.desktop','icon':'firefox-esr','comment':'Web browser'}]):
 d=desktop.Desktop();d.launcher()
 items=d.windows['launcher'].content.findChild(QListWidget)
 assert any(items.item(i).text()=='Firefox ESR' for i in range(items.count()))
 target=next(items.item(i) for i in range(items.count()) if items.item(i).text()=='Firefox ESR')
 with patch.object(desktop,'launch_application') as launch:
  items.itemActivated.emit(target);launch.assert_called_once_with(d,'/usr/share/applications/firefox-esr.desktop')
 with patch.object(host_apps.shutil,'which',return_value='/usr/bin/gio'),patch.object(host_apps.QProcess,'startDetached',return_value=(True,123)) as launch:
  d.showFullScreen();assert host_apps.launch_application(d,'/tmp/test.desktop');assert not d.isFullScreen();launch.assert_called_once_with('/usr/bin/gio',['launch','/tmp/test.desktop'])
 d.close()
print('Unified launcher discovers and launches native apps; fullscreen handoff passed')
