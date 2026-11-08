"""Native-session services. System changes use existing user/polkit permissions."""
import json,os,re,subprocess,sys
from pathlib import Path
FLATHUB='https://dl.flathub.org/repo/flathub.flatpakrepo'
def native():
    if os.environ.get('MACAQUESTEP_SESSION')!='1' or os.environ.get('MACAQUESTEP_NESTED_PREVIEW')=='1':raise ValueError('Use the MacaqueSTEP login session for this action.')
def run(args,timeout=30):return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=timeout)
def lock_session():
    import time
    native()
    session=os.environ.get('XDG_SESSION_ID')
    if not session:raise ValueError('The native session ID is missing; lock readiness cannot be verified.')
    if not os.environ.get('DISPLAY'):raise ValueError('The X11 display is unavailable.')
    run(['light-locker-command','--lock'],10)
    # Require both the locker and logind to report active/locked. Fail closed.
    for _ in range(40):
        active=run(['light-locker-command','--query'],5).strip().lower()
        hint=run(['loginctl','show-session',session,'-p','LockedHint','--value'],5).strip()
        if active=='the screensaver is active' and hint=='yes':return
        time.sleep(.2)
    raise RuntimeError('The lock was not confirmed. Suspend was not requested.')
def action(p):
    op=p.get('action')
    if op=='zones':return {'zones':run(['timedatectl','list-timezones']).splitlines()}
    native()
    if op=='timezone':
        zone=p.get('zone')
        if zone not in run(['timedatectl','list-timezones']).splitlines():raise ValueError('Choose an available time zone.')
        run(['timedatectl','set-timezone',zone]);return {'message':'System time zone updated.'}
    if op=='lock':
        lock_session();return {'message':'The session service confirmed the lock.'}
    if op=='flatpak-launch':
        appid=p.get('id','')
        if not re.fullmatch(r'[A-Za-z0-9_]+(?:\.[A-Za-z0-9_-]+){2,}',appid):raise ValueError('Select a valid application ID.')
        installed=run(['flatpak','list','--user','--app','--columns=application']).splitlines()
        if appid not in [line.strip() for line in installed]:raise ValueError('Select an installed user application.')
        subprocess.Popen(['flatpak','run','--user',appid],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);return {'message':'Application launch requested.'}
    if op=='suspend':
        lock_session() # No suspend unless the real lock confirms readiness.
        run(['systemctl','suspend'],30);return {'message':'Suspend requested after the lock was established.'}
    if op=='lock-status':
        return {'message':run(['loginctl','show-session',os.environ.get('XDG_SESSION_ID','self'),'-p','LockedHint','-p','IdleHint'])+'\n'+run(['systemd-analyze','cat-config','systemd/logind.conf'])[-6000:]}
    if op=='flatpak-enable':args=['flatpak','remote-add','--user','--if-not-exists','flathub',FLATHUB]
    elif op in ('flatpak-search','flatpak-installed','flatpak-updates','flatpak-update','flatpak-install','flatpak-remove'):
        if op=='flatpak-search':
            query=str(p.get('query','')).strip()
            if not query or query.startswith('-') or len(query)>100:raise ValueError('Enter an app name (up to 100 characters).')
            rows=run(['flatpak','search','--user','--columns=application:f,name:f,description:f,remotes:f',query],60).splitlines()
            return {'rows':['\t'.join(row.split('\t')[:3]) for row in rows if len(row.split('\t'))>=4 and 'flathub' in [v.strip() for v in row.split('\t')[3].split(',')]]}
        if op=='flatpak-installed':return {'rows':run(['flatpak','list','--user','--app','--columns=application,name,version']).splitlines()}
        if op=='flatpak-updates':return {'rows':run(['flatpak','remote-ls','--user','--updates','--app','--columns=application,name,version'],60).splitlines()}
        if op=='flatpak-update':args=['flatpak','update','--user','--assumeyes','--noninteractive']
        else:
            appid=p.get('id','')
            if not re.fullmatch(r'[A-Za-z0-9_]+(?:\.[A-Za-z0-9_-]+){2,}',appid):raise ValueError('Select a valid application ID.')
            if op=='flatpak-install':args=['flatpak','install','--user','--assumeyes','--noninteractive','flathub',appid]
            else:
                installed=[row.split('\t')[0].strip() for row in run(['flatpak','list','--user','--app','--columns=application']).splitlines()]
                if appid not in installed:raise ValueError('This app is not installed for your user.')
                args=['flatpak','uninstall','--user','--assumeyes','--noninteractive',appid]
    else:raise ValueError('Unknown service action.')
    output=run(args,600)
    if op=='flatpak-enable':output+=run(['flatpak','update','--user','--appstream','flathub'],600)
    return {'message':output[-24000:] or 'Completed.'}
if __name__=='__main__':
    try:print(json.dumps(action(json.loads(sys.stdin.read(16384)))))
    except Exception as e:print(e.output if isinstance(e,subprocess.CalledProcessError) else str(e),file=sys.stderr);sys.exit(1)
