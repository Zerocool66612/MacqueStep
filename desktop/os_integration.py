"""Visible, logged installer access from the live MacaqueSTEP desktop."""
import os,sys
from pathlib import Path
from PySide6.QtCore import QProcess,QLockFile
from PySide6.QtWidgets import QMessageBox
from installer_center import is_live,log_directory
INSTALLER=Path('/usr/bin/macaquestep-install')
def available():return is_live() and (os.environ.get('MACAQUESTEP_SESSION')=='1' or Path('/usr/share/macaquestep/release').is_file())
def install_system(desktop):
 if not available():QMessageBox.information(desktop,'Install MacaqueSTEP','Boot the MacaqueSTEP live ISO to install to disk.');return
 existing=getattr(desktop,'_installer_center_process',None)
 if existing is not None and existing.state()!=QProcess.NotRunning:QMessageBox.information(desktop,'Installer Center','Installer Center is already open.');return
 was_fullscreen=desktop.isFullScreen()
 # A regular fullscreen preview can obscure independent native installer windows.
 if was_fullscreen:desktop.showNormal();desktop.showMaximized()
 process=QProcess(desktop);desktop._installer_center_process=process;process.setProcessChannelMode(QProcess.MergedChannels);output=[];done=[False]
 def read():
  if not process.isOpen():return
  output.append(bytes(process.readAllStandardOutput()).decode(errors='replace'));output[:]=[''.join(output)[-6000:]]
 def finished(code,*_):
  if done[0]:return
  done[0]=True;read()
  if getattr(desktop,'_installer_center_process',None) is process:desktop._installer_center_process=None
  if was_fullscreen and not desktop.exiting and not installer_center_open():desktop.showFullScreen()
  if code!=0 and not desktop.exiting:QMessageBox.warning(desktop,'Installer Center failed','Installer Center could not finish.\n'+(''.join(output) or process.errorString()))
  process.deleteLater()
 process.readyReadStandardOutput.connect(read);process.finished.connect(finished);process.errorOccurred.connect(lambda error:finished(-1) if error==QProcess.FailedToStart else None);process.start(sys.executable,[str(Path(__file__).with_name('installer_center.py'))])
def installer_center_open():
 path=log_directory()/'installer-center.lock'
 if not path.exists():return False
 lock=QLockFile(str(path))
 if lock.tryLock(0):lock.unlock();return False
 return True
