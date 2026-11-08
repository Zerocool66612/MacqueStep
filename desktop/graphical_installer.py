#!/usr/bin/env python3
"""Graphical per-user desktop-preview installer; never partitions disks."""
import sys,os
from pathlib import Path
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication,QWizard,QWizardPage,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QPlainTextEdit,QMessageBox
class Installer(QWizard):
 def __init__(self):
  super().__init__();self.setWindowTitle('Install MacaqueSTEP 0.23 — Made by Drew');self.resize(680,480);self.proc=None;self.done_ok=False
  page=QWizardPage();page.setTitle('Install MacaqueSTEP desktop preview');layout=QVBoxLayout(page)
  text=QLabel('Install alongside your current desktop. This installs an application and menu launchers for your account. Your notes and settings are kept during upgrades. This wizard does not install a bootable operating system or change disk partitions.');text.setWordWrap(True);layout.addWidget(text)
  self.path=QLineEdit(str(Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'macaquestep-preview'));layout.addWidget(QLabel('Installation directory'));layout.addWidget(self.path)
  self.system=QCheckBox('Use installed Python dependencies (otherwise download into a private environment)');layout.addWidget(self.system);self.addPage(page)
  page=QWizardPage();page.setTitle('Review and install');layout=QVBoxLayout(page);self.review=QLabel();self.review.setWordWrap(True);layout.addWidget(self.review);layout.addWidget(QLabel('Click Next to begin installation. A working internet connection is needed for a private environment.'));self.addPage(page)
  page=QWizardPage();page.setTitle('Installation progress');layout=QVBoxLayout(page);self.log=QPlainTextEdit();self.log.setReadOnly(True);layout.addWidget(self.log);self.result=QLabel();self.result.setWordWrap(True);layout.addWidget(self.result);self.addPage(page)
  self.currentIdChanged.connect(self.changed)
 def changed(self,n):
  if n==1:self.review.setText('MacaqueSTEP 0.23\nMade by Drew\n\nDestination: '+self.path.text()+'\nRuntime: '+('Installed system Python' if self.system.isChecked() else 'Private Python environment')+'\n\nCreates application menu entries and launchers in your account. Existing managed installations can be upgraded. Unmanaged directories are rejected.')
  if n==2 and self.proc is None:self.start_install()
 def start_install(self):
  self.button(QWizard.BackButton).setEnabled(False);self.button(QWizard.FinishButton).setEnabled(False);self.button(QWizard.CancelButton).setEnabled(False)
  self.proc=QProcess(self);self.proc.setProcessChannelMode(QProcess.MergedChannels);self.proc.readyReadStandardOutput.connect(lambda:self.log.appendPlainText(bytes(self.proc.readAllStandardOutput()).decode(errors='replace')));self.proc.finished.connect(self.installation_finished);self.proc.errorOccurred.connect(self.error)
  args=['-u',str(Path(__file__).with_name('install_user.py')),'--prefix',self.path.text()]
  if self.system.isChecked():args.append('--use-system-python')
  self.proc.start(sys.executable,args)
 def installation_finished(self,code,status):
  self.done_ok=code==0 and status==QProcess.NormalExit;self.result.setText('Installed. Open MacaqueSTEP Preview from your applications menu. Close any older preview first.' if self.done_ok else 'Installation failed. Details are shown above. Close this wizard, correct the problem, then try again.');self.button(QWizard.FinishButton).setEnabled(True)
 def error(self,error):
  if error==QProcess.FailedToStart:self.log.appendPlainText(self.proc.errorString());self.installation_finished(1,QProcess.CrashExit)
 def reject(self):
  if self.proc is not None and self.proc.state()!=QProcess.NotRunning:return
  super().reject()
 def closeEvent(self,event):
  if self.proc is not None and self.proc.state()!=QProcess.NotRunning:event.ignore()
  else:super().closeEvent(event)
if __name__=='__main__':
 app=QApplication(sys.argv);w=Installer();w.show();sys.exit(app.exec())
