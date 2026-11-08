"""Run without root, disks, a display, or the installer runtime."""
import importlib.util,sys,types,tempfile,shutil
from pathlib import Path
import yaml
kit=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
calls=[];sys.modules['libcalamares']=types.SimpleNamespace(utils=types.SimpleNamespace(target_env_call=lambda args:calls.append(args) or 0),globalstorage=types.SimpleNamespace(value=lambda name:None))
cleanup=load('cleanup',kit/'config/includes.chroot/usr/lib/calamares/modules/macaquestep-cleanup/main.py')
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder);(root/'etc/lightdm/lightdm.conf.d').mkdir(parents=True);(root/'etc/passwd').write_text('root:x:0:0:root:/root:/bin/bash\nmacaque-live:x:1000:1000::/home/macaque-live:/bin/bash\ndrew:x:1001:1001::/home/drew:/bin/bash\n');(root/'etc/lightdm/lightdm.conf.d/live.conf').write_text('[Seat:*]\nautologin-user=macaque-live\nautologin-user-timeout=0\nuser-session=macaquestep\n')
 (root/'etc/sudoers.d').mkdir();(root/'etc/sudoers.d/live').write_text('temporary');(root/'etc/sudoers.d/drew').write_text('keep')
 cleanup.cleanup(root);assert calls==[['userdel','--force','--remove','macaque-live']];assert 'autologin' not in (root/'etc/lightdm/lightdm.conf.d/live.conf').read_text();assert 'user-session=macaquestep' in (root/'etc/lightdm/lightdm.conf.d/live.conf').read_text();assert (root/'etc/sudoers.d/drew').read_text()=='keep';assert not (root/'etc/sudoers.d/live').exists()
 try:cleanup.cleanup('/');raise AssertionError('accepted real root')
 except ValueError:pass
 (root/'etc/lightdm/lightdm.conf').symlink_to('/etc/passwd')
 try:cleanup.cleanup(root);raise AssertionError('accepted escaping symlink')
 except ValueError:pass
# Optional exact upstream Debian 13 configuration fixture, extracted from its .deb.
if len(sys.argv)>1:
 upstream=Path(sys.argv[1]);configure=load('configure',kit/'config/includes.chroot/usr/share/macaquestep/configure-calamares.py')
 with tempfile.TemporaryDirectory() as folder:
  root=Path(folder);shutil.copytree(upstream/'etc',root/'etc');(root/'etc/os-release').write_text('ID=debian\nVERSION_ID="13"\nPRETTY_NAME="Debian GNU/Linux 13"\n')
  before=yaml.safe_load((root/'etc/calamares/settings.conf').read_text());configure.configure(root);after=yaml.safe_load((root/'etc/calamares/settings.conf').read_text());assert after['branding']=='macaquestep' and after['prompt-install'] is True
  tasks=next(p['exec'] for p in after['sequence'] if 'exec' in p);assert tasks.index('users')<tasks.index('macaquestep-cleanup')<tasks.index('displaymanager');assert tasks.index('bootloader')<tasks.index('initramfs')<tasks.index('umount')
  oldtasks=next(p['exec'] for p in before['sequence'] if 'exec' in p);assert [t for t in tasks if t!='macaquestep-cleanup']==oldtasks
  assert 'ID=debian' in (root/'etc/os-release').read_text()
  dm=yaml.safe_load((root/'etc/calamares/modules/displaymanager.conf').read_text());assert dm['defaultDesktopEnvironment']['desktopFile']=='macaquestep'
print('PASS target-only cleanup, symlink/root rejection, live account isolation and upstream installer sequence preservation')
