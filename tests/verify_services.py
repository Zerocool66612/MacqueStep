import os,sys,tempfile,json,zipfile
from pathlib import Path
from unittest.mock import patch
root=Path(tempfile.mkdtemp());os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config');os.environ['XDG_STATE_HOME']=str(root/'state');sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
import desktop_services as services
from personal_backups import create_backup,recover_backup
from service_panels import validate_preferences
# No service change may escape the native-session guard.
with patch.dict(os.environ,{'MACAQUESTEP_SESSION':'0'}):
 try:services.action({'action':'flatpak-update'});raise AssertionError('unguarded')
 except ValueError:pass
with patch.dict(os.environ,{'MACAQUESTEP_SESSION':'1','XDG_SESSION_ID':'1','DISPLAY':':99'}):
 calls=[]
 def run(args,timeout=30):
  calls.append(args)
  if args[0]=='light-locker-command' and '--query' in args:return 'The screensaver is active\n'
  if args[0]=='loginctl':return 'yes\n'
  return ''
 with patch.object(services,'run',run):services.action({'action':'suspend'})
 assert calls[-1]==['systemctl','suspend'] and calls.index(['systemctl','suspend'])>calls.index(['light-locker-command','--query'])
 with patch.object(services,'lock_session',side_effect=RuntimeError('not locked')),patch.object(services,'run') as run:
  try:services.action({'action':'suspend'});raise AssertionError('suspended without lock')
  except RuntimeError:pass
  run.assert_not_called()
 with patch.object(services,'run') as run:
  for op,payload in [('flatpak-search',{'query':'--bad'}),('flatpak-install',{'id':'bad;command'}),('flatpak-launch',{'id':'bad;command'})]:
   try:services.action({'action':op,**payload});raise AssertionError('invalid input')
   except ValueError:pass
  run.assert_not_called()
 with patch.object(services,'run',return_value='com.example.App\tExample\tDescription\tflathub\ncom.other.App\tOther\tOther\tuntrusted\n'):
  assert services.action({'action':'flatpak-search','query':'example'})['rows']==['com.example.App\tExample\tDescription']
source=root/'Documents';source.mkdir();(source/'note.txt').write_text('preserve');(source/'.secret').write_text('omit');(source/'alias').symlink_to('/etc/passwd');archive=root/'personal.zip';create_backup(source,{'theme':'Dark'},archive,True);out=Path(recover_backup(archive,root/'recovered'));assert (out/'Personal Files/note.txt').read_text()=='preserve';assert not (out/'Personal Files/.secret').exists();assert not (out/'Personal Files/alias').exists();assert (source/'note.txt').read_text()=='preserve'
try:create_backup(source,{},archive,True);raise AssertionError('overwrote backup')
except ValueError:pass
bad=root/'bad.zip'
with zipfile.ZipFile(bad,'w') as z:z.writestr('../escape','bad')
try:recover_backup(bad,root/'recovered');raise AssertionError('traversal')
except ValueError:pass
assert validate_preferences({'theme':'Classic','text_size':18,'startup_command':'bad'})=={'theme':'Classic','text_size':18}
for bad in ({'text_size':99},{'high_contrast':'yes'},{'theme':'invalid'}):
 try:validate_preferences(bad);raise AssertionError('invalid preferences')
 except ValueError:pass
# UI creation/actions, accessibility, busy-window shutdown guards.
from desktop import *
from PySide6.QtTest import QTest
app=QApplication([]);d=Desktop();d.show();QTest.qWait(200)
try:
 for method in (d.setup_assistant,d.software_center,d.accessibility_panel,d.lock_sleep,d.personal_recovery):assert method() is not None
 panel=d.windows['setup'].content;panel.mode.setCurrentText('Classic');panel.side.setCurrentText('Right');panel.appearance();assert d.theme=='Classic'
 panel.pages.setCurrentIndex(2);panel.advance();assert d.settings.value('setup_completed',False,type=bool)
 access=d.windows['accessibility'].content;access.size.setValue(18);access.contrast.setChecked(True);access.motion.setChecked(True);access.apply();assert d.settings.value('text_size',0,type=int)==18;assert 'font-size:18px' in d.styleSheet();assert d.settings.value('reduce_motion',False,type=bool)
 busy=d.windows['software'];busy.content.job=object();busy.close();assert busy in d.windows.values();busy.content.job=None
 d.show_left_app_menu();d.side_app_menu.populate('Tools');assert any(a.text()=='Software Center' for a in d.side_app_menu.menus['Tools'].actions())
 QTest.qWait(150);d.grab().save('/tmp/step020-services.png')
finally:d.close();QTest.qWait(50)
print('PASS native guards, lock-before-suspend and fail-closed behavior, Flatpak validation/filtering, personal backups/recovery, preference allowlist, setup/accessibility/menu integration and busy close guards')
