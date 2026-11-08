"""Visible network access without relying on a system tray."""
import shutil
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit

class NetworkPanel(QWidget):
 def __init__(self, desktop):
  super().__init__();self.desktop=desktop;self.jobs=[]
  layout=QVBoxLayout(self)
  note=QLabel('Connect to Wi-Fi using Activate a connection. Network settings lets you edit saved connections. A missing wireless adapter may require firmware.');note.setWordWrap(True);layout.addWidget(note)
  for title,program,args in [('Connect to Wi-Fi…','xterm',['-T','Wi-Fi & Network','-e','nmtui-connect']),('Network settings…','nm-connection-editor',[])]:
   button=QPushButton(title);button.setEnabled(bool(shutil.which(program)) and (program!='xterm' or bool(shutil.which('nmtui-connect'))));button.clicked.connect(lambda checked=False,p=program,a=args:self.launch(p,a));layout.addWidget(button)
  self.output=QPlainTextEdit();self.output.setReadOnly(True);layout.addWidget(self.output)
  refresh=QPushButton('Refresh connection status');refresh.clicked.connect(self.refresh);layout.addWidget(refresh)
  copy=QPushButton('Copy network diagnostics');copy.clicked.connect(self.output.selectAll);copy.clicked.connect(self.output.copy);layout.addWidget(copy);self.refresh()
 def launch(self,program,args):
  result=QProcess.startDetached(shutil.which(program) or program,args)
  if result[0]:
   if self.desktop.isFullScreen():self.desktop.showNormal();self.desktop.showMaximized()
  else:self.output.appendPlainText('Unable to open '+program)
 def refresh(self):
  if self.jobs:return
  self.output.clear()
  for program,args in [('nmcli',['device','status']),('rfkill',['list'])]:
   executable=shutil.which(program)
   if not executable:self.output.appendPlainText(program+' is unavailable');continue
   process=QProcess(self);self.jobs.append(process);process.setProcessChannelMode(QProcess.MergedChannels)
   timer=QTimer(process);timer.setSingleShot(True);timer.timeout.connect(process.kill)
   def finish(code=0,status=None,p=process,label=program):
    if p not in self.jobs:return
    self.output.appendPlainText(label+':\n'+bytes(p.readAllStandardOutput()).decode(errors='replace')+ ('\nCommand failed or timed out' if code else ''))
    self.jobs.remove(p);p.deleteLater()
   process.finished.connect(finish);process.errorOccurred.connect(lambda error,p=process,f=finish:f(-1) if error==QProcess.FailedToStart else None);process.start(executable,args);timer.start(5000)
 def shutdown(self):
  for process in list(self.jobs):process.kill();process.waitForFinished(500)
  return True
