import os,tempfile,sys
from pathlib import Path
root=Path(tempfile.mkdtemp());os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_CONFIG_HOME']=str(root/'config');os.environ['XDG_DATA_HOME']=str(root/'data');sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from desktop import *
from PySide6.QtTest import QTest
from PySide6.QtCore import QProcess
from unittest.mock import patch
import os_integration
app=QApplication([]);d=Desktop();d.show();QTest.qWait(150)
with patch.object(os_integration,'available',return_value=True):
 d.side_app_menu.populate('Tools');items=d.side_app_menu.menus['Tools'].actions();assert items[0].text()=='Install MacaqueSTEP…';d.preferences();assert any(b.text()=='Install MacaqueSTEP to disk…' for b in d.windows['preferences'].content.findChildren(QPushButton))
 with patch.object(QProcess,'start') as start:items[0].trigger();assert start.called
 d._installer_center_process=None
with patch.object(os_integration,'available',return_value=False):d.side_app_menu.populate('Tools');assert not any('Install MacaqueSTEP' in a.text() for a in d.side_app_menu.menus['Tools'].actions())
d.close();QTest.qWait(40);print('PASS live-only installer menu, Preferences integration and guarded launch')
