"""Bounded asynchronous system commands, with no shell interpolation."""
import json,sys
from pathlib import Path
from PySide6.QtCore import QObject,QProcess,QProcessEnvironment,QTimer,Signal
class Task(QObject):
    done=Signal(bool,str)
    def __init__(self,parent,argv,payload=None,timeout=25000):
        super().__init__(parent);self.process=QProcess(self);self.finished=False
        env=QProcessEnvironment.systemEnvironment();env.insert('LC_ALL','C');self.process.setProcessEnvironment(env)
        self.process.finished.connect(self.finish);self.process.errorOccurred.connect(self.failed)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.expire);self.timer.start(timeout)
        if payload is not None:
            data=json.dumps(payload).encode()
            def send():self.process.write(data);self.process.closeWriteChannel()
            self.process.started.connect(send)
        self.process.start(argv[0],argv[1:])
    def complete(self,ok,text):
        if self.finished:return
        self.finished=True;self.timer.stop();self.done.emit(ok,text);self.deleteLater()
    def finish(self,code,*_):
        out=bytes(self.process.readAllStandardOutput()).decode(errors='replace');err=bytes(self.process.readAllStandardError()).decode(errors='replace')
        self.complete(code==0,(out if code==0 else err or out or 'The system service rejected this request.').strip()[:200000])
    def failed(self,*_):
        if self.process.error()==QProcess.FailedToStart:self.complete(False,'Could not start '+self.process.program()+': '+self.process.errorString())
    def expire(self):self.process.kill();self.complete(False,'The request timed out. Check the system service and try again.')
    def cancel(self):
        if self.process.state()!=QProcess.NotRunning:self.process.kill();self.process.waitForFinished(1000)
    @staticmethod
    def helper(name):return [sys.executable,str(Path(__file__).with_name(name))]
