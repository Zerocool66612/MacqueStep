#!/usr/bin/env python3
"""Visible live installer preflight, authorization, process status and local logs."""
import os,sys,json,shutil,subprocess
from pathlib import Path
from PySide6.QtCore import Qt,QProcess,QProcessEnvironment,QLockFile,QTimer
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPlainTextEdit,QPushButton,QMessageBox,QFileDialog
SOURCES=('/run/live/medium/live/filesystem.squashfs','/lib/live/mount/medium/live/filesystem.squashfs')
HELPER='/usr/lib/macaquestep/installer-root'
def is_live():
 try:return 'boot=live' in Path('/proc/cmdline').read_text().split()
 except OSError:return False
def source_image():return next((s for s in SOURCES if Path(s).is_file()),None)
def preflight():
 errors=[];checks={'live_session':is_live(),'source_image':source_image(),'display':os.environ.get('DISPLAY',''),'calamares':shutil.which('calamares'),'root_helper':Path(HELPER).is_file(),'settings':Path('/etc/calamares/settings.conf').is_file(),'sudo':shutil.which('sudo'),'pkexec':shutil.which('pkexec')}
 if not checks['live_session']:errors.append('Boot the MacaqueSTEP live ISO to install to disk.')
 if not checks['source_image']:errors.append('The live filesystem image was not found. Reboot with the ISO/USB still connected.')
 if not checks['display']:errors.append('An X11 display is not available. Start from the live graphical desktop.')
 if not checks['calamares'] or not checks['root_helper'] or not checks['settings']:errors.append('Installer components are missing. Use the rebuilt 0.23 ISO or install the matching update package in this live session.')
 if not checks['sudo'] and not checks['pkexec']:errors.append('No installer authorization tool is available.')
 return checks,errors
def installer_command():
 # The live account normally has passwordless sudo. Other sessions use polkit.
 sudo=shutil.which('sudo')
 if sudo:
  try:
   if subprocess.run([sudo,'-n','true'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3).returncode==0:return [sudo,'-n','--preserve-env=DISPLAY,XAUTHORITY',HELPER]
  except (OSError,subprocess.TimeoutExpired):pass
 pkexec=shutil.which('pkexec')
 if pkexec:return [pkexec,HELPER]
 raise RuntimeError('Installer authorization is unavailable. Start from the MacaqueSTEP live session.')
def log_directory():
 root=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'macaquestep';root.mkdir(parents=True,exist_ok=True);return root
class InstallerCenter(QWidget):
 def __init__(self):
  super().__init__();self.setWindowTitle('Install MacaqueSTEP — Made by Drew');self.resize(850,600);self.process=None;self.access_granted=False;self.running=False;self.log=log_directory()/'installer-launch.log';self.log_file=None
  v=QVBoxLayout(self);note=QLabel('Install MacaqueSTEP to a disk using Calamares. Start the installer, choose your disk and account, and review its final summary before applying changes. Keep this window open while it runs.');note.setWordWrap(True);v.addWidget(note)
  self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status);self.output=QPlainTextEdit();self.output.setReadOnly(True);self.output.setMaximumBlockCount(6000);v.addWidget(self.output,1)
  row=QHBoxLayout();v.addLayout(row);self.start=QPushButton('Start graphical disk installer');self.start.clicked.connect(self.launch);row.addWidget(self.start);self.refresh=QPushButton('Check again');self.refresh.clicked.connect(self.check);row.addWidget(self.refresh);copy=QPushButton('Copy diagnostic text');copy.clicked.connect(lambda:QApplication.clipboard().setText(self.output.toPlainText()));row.addWidget(copy);save=QPushButton('Save log…');save.clicked.connect(self.save_log);row.addWidget(save);self.check()
 def append(self,text):
  self.output.appendPlainText(text)
  if self.log_file:
   try:self.log_file.write(text+'\n');self.log_file.flush()
   except OSError:pass
 def check(self):
  if self.running:return
  checks,errors=preflight();self.output.setPlainText(json.dumps(checks,indent=2));self.start.setEnabled(not errors);self.status.setText('\n'.join(errors) if errors else 'Ready. Calamares will open in its own window. Installation currently needs an internet connection.')
 def launch(self):
  if self.running:return
  checks,errors=preflight()
  if errors:self.check();return
  try:
   command=installer_command();self.log_file=self.log.open('w',encoding='utf-8');os.chmod(self.log,0o600);self.log_file.write(json.dumps(checks,indent=2)+'\n');self.log_file.flush()
  except (OSError,RuntimeError) as error:self.status.setText(str(error));return
  # Grant only the local root account access to this X11 display for the GUI.
  try:
   result=subprocess.run(['xhost','+si:localuser:root'],capture_output=True,text=True,timeout=3)
   if result.returncode:self.append('Display authorization: '+result.stderr.strip())
   else:self.access_granted=True
  except (OSError,subprocess.TimeoutExpired) as error:self.append('Display authorization warning: '+str(error))
  self.process=QProcess(self);self.process.setProcessChannelMode(QProcess.MergedChannels);environment=QProcessEnvironment.systemEnvironment();environment.insert('QT_QPA_PLATFORM','xcb');self.process.setProcessEnvironment(environment);self.process.readyReadStandardOutput.connect(self.read);self.process.finished.connect(self.completed);self.process.errorOccurred.connect(self.error);self.running=True;self.start.setEnabled(False);self.refresh.setEnabled(False);self.status.setText('Installer running. Use the Calamares window to continue or cancel.');self.append('Starting: '+command[0]+' → MacaqueSTEP installer helper');self.process.start(command[0],command[1:])
 def read(self):
  if not self.process.isOpen():return
  text=bytes(self.process.readAllStandardOutput()).decode(errors='replace').rstrip()
  if text:self.append(text)
 def revoke(self):
  if self.access_granted:
   try:subprocess.run(['xhost','-si:localuser:root'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
   except (OSError,subprocess.TimeoutExpired):pass
   self.access_granted=False
 def completed(self,code,status):
  if not self.running:return
  self.read();self.running=False;self.revoke();self.start.setEnabled(True);self.refresh.setEnabled(True)
  if status==QProcess.NormalExit and code==0:self.status.setText('Calamares closed. Its own final page determines whether installation completed or was canceled. Log: '+str(self.log))
  else:self.status.setText(f'Installer exited with code {code}. The log below shows the failure; use Copy diagnostic text or Save log.')
  self.append(f'Installer exit code: {code}')
  if self.log_file:self.log_file.close();self.log_file=None
 def error(self,error):
  if error==QProcess.FailedToStart:self.append(self.process.errorString());self.completed(-1,QProcess.CrashExit)
 def save_log(self):
  destination=QFileDialog.getSaveFileName(self,'Save installer diagnostics',str(Path.home()/'MacaqueSTEP-installer.log'),'Log (*.log)')[0]
  if destination:
   try:Path(destination).write_text(self.output.toPlainText());self.status.setText('Log saved: '+destination)
   except OSError as error:self.status.setText(str(error))
 def closeEvent(self,event):
  if self.running:QMessageBox.information(self,'Installer running','Finish or cancel in Calamares before closing this window.');event.ignore();return
  self.revoke();super().closeEvent(event)
if __name__=='__main__':
 app=QApplication(sys.argv);app.setStyle('Fusion');lock=QLockFile(str(log_directory()/'installer-center.lock'))
 if not lock.tryLock(0):QMessageBox.information(None,'Install MacaqueSTEP','The Installer Center is already open.');sys.exit(0)
 app.aboutToQuit.connect(lock.unlock);window=InstallerCenter();window.show();sys.exit(app.exec())
