#!/usr/bin/env python3
import os,platform,shutil,sys,json,subprocess
from pathlib import Path
required='lb debootstrap dpkg-deb xorriso mksquashfs mtools grub-mkstandalone'.split()
# mtools is a package rather than executable on some systems; mcopy is its check.
required[required.index('mtools')]='mcopy'
missing=[x for x in required if not shutil.which(x)]
status=Path('/proc/self/status').read_text();caps=int(next(x.split()[1] for x in status.splitlines() if x.startswith('CapEff:')),16)
report={'architecture':platform.machine(),'root':os.geteuid()==0,'can_mount':bool(caps&(1<<21)),'free_gib':round(shutil.disk_usage('.').free/1024**3,1),'missing_tools':missing}
print(json.dumps(report,indent=2))
errors=[]
if platform.machine() not in ('x86_64','amd64'):errors.append('Use an amd64 build machine or VM.')
if os.geteuid()!=0:errors.append('Run the build using sudo in a dedicated build VM.')
if not report['can_mount']:errors.append('CAP_SYS_ADMIN is missing; live-build cannot mount its chroot here.')
if report['free_gib']<20:errors.append('Allow at least 20 GiB of free build space.')
if missing:errors.append('Install the missing live-build dependencies listed above.')
if shutil.which('lb'):
 help_text=subprocess.run(['lb','config','--help'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout
 unsupported=[flag for flag in ('--updates','--bootloaders','--uefi-secure-boot') if flag not in help_text]
 if unsupported:errors.append('This live-build is too old for the image configuration: '+', '.join(unsupported)+'. Install Debian trixie live-build as described in README.md.')
for e in errors:print(e,file=sys.stderr)
sys.exit(bool(errors))
