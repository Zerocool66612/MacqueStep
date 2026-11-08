import os,sys,tempfile
from pathlib import Path
root=Path(tempfile.mkdtemp());os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config');sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from decorations import *
from PySide6.QtTest import QTest
from PySide6.QtCore import QProcess
from graphical_installer import Installer
from unittest.mock import patch
app=QApplication([]);d=Desktop();d.show();QTest.qWait(150);w=d.windows['files'];key=w.property('running_key')
for theme in ('Classic','Light','Dark'):
 d.apply_theme(theme)
 for style in STYLES:
  d.settings.setValue('decoration_style',style);apply_decorations(d);QTest.qWait(10)
  assert w.titlebar.property('decorationStyle')==style
  assert all(c.accessibleName() for c in w.titlebar.controls.values())
  w.titlebar.controls['minimize'].click();QTest.qWait(10);assert w.isMinimized();d.reopen(key)
  w.titlebar.controls['maximize'].click();QTest.qWait(10);assert w.isMaximized();w.titlebar.controls['maximize'].click();assert not w.isMaximized()
 d.set_top_bar_visible(False);assert d.side_app_menu.isVisible()
d.settings.setValue('titlebar_height',44);d.settings.setValue('decoration_zoom',False);apply_decorations(d);assert w.titlebar.height()==44 and w.titlebar.controls['maximize'].isHidden()
d.resize_preview_window(w,480,320);assert w.width()==480 and w.height()==320
d.preferences();assert d.windows['preferences'].content.findChild(QComboBox,'decorationStyle')
# Close uses the existing discard guard; a cancelled close keeps the editor.
e=d.editor();e.content.editor.setPlainText('unsaved');e.content.editor.document().setModified(True)
with patch.object(QMessageBox,'question',return_value=QMessageBox.No):e.titlebar.controls['close'].click();assert e in d.windows.values()
e.content.editor.document().setModified(False);e.titlebar.controls['close'].click();QTest.qWait(20);assert e not in d.windows.values()
# Exercise wizard success/failure completion independently of installation.
i=Installer();i.installation_finished(1,QProcess.NormalExit);assert not i.done_ok and 'failed' in i.result.text();i.installation_finished(0,QProcess.NormalExit);assert i.done_ok and 'Installed.' in i.result.text();i.close()
d.close();QTest.qWait(30);print('Decoration and installer UI checks passed')
