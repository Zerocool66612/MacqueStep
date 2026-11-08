#!/usr/bin/env python3
"""Original first-installed-login welcome. Never shown in a live session."""
import hashlib,json,os,sys
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QElapsedTimer,QRectF,QSaveFile,QIODevice,QLockFile,QUrl,QSettings
from PySide6.QtGui import QPainter,QColor,QLinearGradient,QFont
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtMultimedia import QSoundEffect
DURATION=15000

def installation_token(marker=Path('/etc/macaquestep-installed'),cmdline=Path('/proc/cmdline')):
 try:
  if 'boot=live' in cmdline.read_text().split():return None
  content=marker.read_bytes()
  if not content.strip():return None
  return hashlib.sha256(content).hexdigest()
 except OSError:return None

def state_directory():
 return Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'macaquestep'

def claim_first_login(token,directory):
 """Consume once before playing, so interrupted sessions cannot cause repeat loops."""
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 lock=QLockFile(str(directory/'welcome.lock'))
 if not lock.tryLock(0):return False
 try:
  receipt=directory/'welcome-seen.json'
  try:
   if json.loads(receipt.read_text()).get('installation')==token:return False
  except (OSError,ValueError,AttributeError):pass
  output=QSaveFile(str(receipt));data=json.dumps({'installation':token,'status':'first-login-consumed','version':1}).encode()
  if not output.open(QIODevice.WriteOnly) or output.write(data)!=len(data) or not output.commit():return False
  (directory/'setup-pending').write_text(token)
  return True
 finally:lock.unlock()

def smooth(v):
 v=max(0.0,min(1.0,v));return v*v*(3-2*v)

class Welcome(QWidget):
 def __init__(self):
  super().__init__();self.setWindowTitle('Welcome to MacaqueSTEP');self.setWindowFlags(Qt.Window|Qt.FramelessWindowHint);self.setFocusPolicy(Qt.StrongFocus)
  self.elapsed=QElapsedTimer();self.elapsed.start();self.position=None
  self.logo=QSvgRenderer(str(Path(__file__).with_name('assets')/'monkey.svg'),self)
  self.completed=False;self.started=False;self.reduce_motion=QSettings('MacaqueSTEP','DesktopPreview').value('reduce_motion',False,type=bool)
  self.music=QSoundEffect(self);self.music.setSource(QUrl.fromLocalFile(str(Path(__file__).with_name('assets')/'sounds/welcome.wav')));self.music.setVolume(.5)
  self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(16)
 def showEvent(self,event):
  super().showEvent(event)
  if not self.started:self.started=True;self.elapsed.start();QTimer.singleShot(250,self.music.play)
 def tick(self):
  if self.elapsed.elapsed()>=DURATION:self.completed=True;self.close()
  else:self.update()
 def keyPressEvent(self,event):event.accept()
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);w=self.width();h=self.height();t=8 if self.reduce_motion else (self.position if self.position is not None else self.elapsed.elapsed())/1000
  gradient=QLinearGradient(0,0,w,h);gradient.setColorAt(0,QColor('#101827'));gradient.setColorAt(.55,QColor('#24394b'));gradient.setColorAt(1,QColor('#183e40'));p.fillRect(self.rect(),gradient)
  # Quiet concentric arcs echo a workstation display, without copied video assets.
  for i in range(5):
   p.setPen(QColor(116,213,197,12+i*3));radius=min(w,h)*(.26+i*.11);p.drawEllipse(QRectF(w*.5-radius,h*.43-radius,radius*2,radius*2))
  hello_alpha=smooth(t/.8)*(1-smooth((t-4.8)/.8))
  if hello_alpha>0:
   p.save();p.setOpacity(hello_alpha);font=QFont('URW Chancery L',max(40,int(min(w,h)*.16)));font.setItalic(True);p.setFont(font);p.setPen(QColor('#f1f5f9'))
   rect=QRectF(w*.1,h*.29,w*.8,h*.28);p.setClipRect(QRectF(rect.left(),rect.top(),rect.width()*smooth((t-.25)/2.3),rect.height()));p.drawText(rect,Qt.AlignCenter,'hello');p.restore()
  alpha=smooth((t-5.2)/1.1)
  if alpha:
   p.save();p.setOpacity(alpha);size=min(w,h)*.18;self.logo.render(p,QRectF((w-size)/2,h*.2,size,size));p.setPen(QColor('#f1f5f9'));p.setFont(QFont('DejaVu Sans',max(20,int(min(w,h)*.043)),QFont.DemiBold));p.drawText(QRectF(24,h*.44,w-48,h*.12),Qt.AlignCenter,'Welcome to MacaqueSTEP')
   p.setPen(QColor('#bfd5dd'));p.setFont(QFont('DejaVu Sans',max(12,int(min(w,h)*.023))));p.drawText(QRectF(24,h*.56,w-48,h*.07),Qt.AlignCenter,'Made by Drew');p.restore()
  p.setPen(QColor('#8da9b4'));p.setFont(QFont('DejaVu Sans',11));p.drawText(QRectF(24,h-64,w*.6,32),Qt.AlignLeft|Qt.AlignVCenter,'Your desktop is ready.');p.end()
 def closeEvent(self,event):
  if not self.completed:event.ignore();return
  self.timer.stop();self.music.stop();super().closeEvent(event)

def main():
 token=installation_token()
 if token is None:return 0
 app=QApplication(sys.argv)
 if not claim_first_login(token,state_directory()):return 0
 app.setStyle('Fusion');welcome=Welcome();welcome.showFullScreen();welcome.activateWindow();welcome.setFocus();return app.exec()
if __name__=='__main__':sys.exit(main())
