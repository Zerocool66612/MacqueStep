"""Read-only host inventory, explicitly not a conformance test or certification."""
import json,os,platform,shutil
from datetime import datetime,timezone
from PySide6.QtCore import QSaveFile,QIODevice
from PySide6.QtWidgets import *
UTILITIES='sh awk basename cat chmod chown cmp comm cp cut date dd df diff dirname du echo env expr false file find getconf grep head id kill ln locale ls mkdir mkfifo mv nice nohup od paste pathchk printf ps pwd readlink rm rmdir sed sleep sort stty tail tee test time touch tr true tty uname uniq wc xargs'.split()
def inventory():
 values={}
 for name in ('SC_VERSION','SC_2_VERSION','SC_XOPEN_VERSION','SC_THREADS','SC_SEMAPHORES','SC_TIMERS','SC_MAPPED_FILES','SC_JOB_CONTROL','SC_SAVED_IDS'):
  try:values[name]=os.sysconf(name)
  except (ValueError,OSError):values[name]='Unavailable'
 return {'format':1,'created_utc':datetime.now(timezone.utc).isoformat(),'status':'Inventory only; full POSIX/SUS conformance has not been tested.','target':'POSIX.1-2024 / SUS Version 5 — proposed engineering target, not verified','host':{'system':platform.system(),'release':platform.release(),'architecture':platform.machine(),'libc':list(platform.libc_ver())},'reported_sysconf':values,'utilities':{name:shutil.which(name) for name in UTILITIES},'remaining':['Select and freeze the actual OS release and supported configuration.','Map every applicable standard requirement to implementation and evidence.','Test C interfaces, headers, shell and utility semantics, locales, and error behavior.','Investigate and fix failures; document options and implementation-defined behavior.','Repeat validation on the installed image and target hardware.']}
def save_report(path,report):
 data=json.dumps(report,indent=2).encode();file=QSaveFile(str(path))
 if not file.open(QIODevice.WriteOnly) or file.write(data)!=len(data) or not file.commit():raise OSError(file.errorString())
class Readiness(QWidget):
 def __init__(self):
  super().__init__();v=QVBoxLayout(self);note=QLabel('This inventories the host running MacaqueSTEP. A detected utility or reported POSIX version does not prove standards conformance. The full OS has not been certified or fully tested.');note.setWordWrap(True);v.addWidget(note);self.text=QPlainTextEdit();self.text.setReadOnly(True);v.addWidget(self.text,1);row=QHBoxLayout()
  for title,callback in [('Refresh inventory',self.refresh),('Export JSON…',self.export)]:button=QPushButton(title);button.clicked.connect(callback);row.addWidget(button)
  v.addLayout(row);self.status=QLabel();v.addWidget(self.status);self.refresh()
 def refresh(self):
  self.report=inventory();found=sum(bool(value) for value in self.report['utilities'].values());self.text.setPlainText(json.dumps(self.report,indent=2));self.status.setText(f'{found}/{len(UTILITIES)} sampled utilities found. Behavior remains untested.')
 def export(self):
  path=QFileDialog.getSaveFileName(self,'Export host inventory','macaquestep-unix-inventory.json','JSON (*.json)')[0]
  if path:
   try:save_report(path,self.report);self.status.setText('Inventory exported.')
   except OSError as error:QMessageBox.warning(self,'Export failed',str(error))
