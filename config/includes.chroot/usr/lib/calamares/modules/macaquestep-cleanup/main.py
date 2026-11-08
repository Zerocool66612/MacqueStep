"""Clean live-only state inside Calamares' mounted installation target."""
from pathlib import Path
import libcalamares

def pretty_name():return 'Prepare MacaqueSTEP login and remove live-only settings'
def cleanup(root):
 root=Path(root).resolve()
 if root==Path('/') or not (root/'etc/passwd').is_file():raise ValueError('Refusing an invalid installation target')
 def target(relative):
  p=root/relative
  if not p.resolve().is_relative_to(root):raise ValueError('Target path leaves installation root: '+relative)
  return p
 # Live autologin must be removed before displaymanager configures the new account.
 files=[target('etc/lightdm/lightdm.conf')]
 directory=target('etc/lightdm/lightdm.conf.d')
 if directory.is_dir():files+=list(directory.glob('*.conf'))
 for p in files:
  if p.exists():
   if not p.resolve().is_relative_to(root):raise ValueError('Unsafe login configuration')
   lines=p.read_text().splitlines();p.write_text('\n'.join(line for line in lines if not line.strip().startswith(('autologin-user=','autologin-user-timeout=')))+'\n')
 for rel in ('etc/sudoers.d/live','etc/live/config.conf.d/50-macaquestep.conf','usr/share/applications/macaquestep-install.desktop','usr/bin/macaquestep-install'):
  p=target(rel)
  if p.is_file():p.unlink()
 passwd=target('etc/passwd').read_text().splitlines()
 if any(line.startswith('macaque-live:') for line in passwd):
  result=libcalamares.utils.target_env_call(['userdel','--force','--remove','macaque-live'])
  if result:raise RuntimeError('Could not remove the temporary live account')
 # LightDM's packaged unit is enabled by the image; retain the session default.
 import json,uuid
 target('etc/macaquestep-installed').write_text(json.dumps({'name':'MacaqueSTEP','version':'0.23','installation_id':str(uuid.uuid4()),'credit':'Made by Drew'})+'\n')
def run():
 try:
  root=libcalamares.globalstorage.value('rootMountPoint')
  if not root:return ('Installation target missing','No rootMountPoint was provided.')
  cleanup(root)
 except Exception as e:return ('MacaqueSTEP target preparation failed',str(e))
 return None
