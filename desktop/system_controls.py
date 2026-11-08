import shutil,re
from pathlib import Path
from PySide6.QtCore import Qt,QProcess,QTimer
from PySide6.QtWidgets import *
class SystemControls(QWidget):
 def __init__(self):
  super().__init__();self.jobs=[];self.closing=False;v=QVBoxLayout(self);self.status=QLabel('Controls use detected host utilities and your existing permissions.');self.status.setWordWrap(True);v.addWidget(self.status);form=QFormLayout();v.addLayout(form);self.volume=QSlider(Qt.Horizontal);self.volume.setRange(0,100);self.volume.setValue(50);self.vol_label=QLabel('Audio backend: unavailable');self.brightness=QSlider(Qt.Horizontal);self.brightness.setRange(1,100);self.brightness.setValue(50);self.bri_label=QLabel('Brightness: unavailable');form.addRow('Volume',self.volume);form.addRow(self.vol_label);mute=QPushButton('Toggle mute');form.addRow(mute);form.addRow('Screen brightness',self.brightness);form.addRow(self.bri_label)
  self.audio='wpctl' if shutil.which('wpctl') else 'pactl' if shutil.which('pactl') else None;self.volume.setEnabled(bool(self.audio));mute.setEnabled(bool(self.audio));self.brightness.setEnabled(bool(shutil.which('brightnessctl')));self.volume.sliderReleased.connect(self.set_volume);mute.clicked.connect(self.mute);self.brightness.sliderReleased.connect(self.set_brightness)
  for title,candidates in [('Network connections',['nm-connection-editor','connman-gtk']),('Bluetooth settings',['blueman-manager'])]:
   program=next((shutil.which(name) for name in candidates if shutil.which(name)),None);button=QPushButton(title if program else title+' — unavailable');button.setEnabled(bool(program));button.clicked.connect(lambda checked=False,p=program:QProcess.startDetached(p,[]) if p else None);v.addWidget(button)
  self.battery=QLabel();self.battery.setWordWrap(True);v.addWidget(self.battery);refresh=QPushButton('Refresh status');refresh.clicked.connect(self.refresh);v.addWidget(refresh);v.addStretch();self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(30000);self.refresh()
 def command(self,program,args,callback=None):
  if self.closing:return
  executable=shutil.which(program)
  if not executable:self.status.setText(program+' is unavailable.');return
  process=QProcess(self);self.jobs.append(process);process.setProcessChannelMode(QProcess.MergedChannels);timeout=QTimer(process);timeout.setSingleShot(True);timeout.timeout.connect(process.kill)
  def done(code,*_):
   text=bytes(process.readAllStandardOutput()).decode(errors='replace').strip()
   if code:self.status.setText(program+': '+(text or 'command failed or timed out'))
   elif callback:callback(text)
   else:self.status.setText('Updated host control.');QTimer.singleShot(150,self.refresh)
   if process in self.jobs:self.jobs.remove(process)
   process.deleteLater()
  def failed(error):
   self.status.setText(process.errorString())
   if error==QProcess.FailedToStart:
    if process in self.jobs:self.jobs.remove(process)
    process.deleteLater()
  process.finished.connect(done);process.errorOccurred.connect(failed);process.start(executable,args);timeout.start(4000)
 def set_volume(self):
  if self.audio=='wpctl':self.command('wpctl',['set-volume','@DEFAULT_AUDIO_SINK@',str(self.volume.value()/100)])
  elif self.audio=='pactl':self.command('pactl',['set-sink-volume','@DEFAULT_SINK@',str(self.volume.value())+'%'])
 def mute(self):
  if self.audio=='wpctl':self.command('wpctl',['set-mute','@DEFAULT_AUDIO_SINK@','toggle'])
  elif self.audio=='pactl':self.command('pactl',['set-sink-mute','@DEFAULT_SINK@','toggle'])
 def set_brightness(self):self.command('brightnessctl',['set',str(self.brightness.value())+'%'])
 def refresh(self):
  if self.closing:return
  if self.audio=='wpctl':
   def audio(text):
    match=re.search(r'Volume:\s*([0-9.]+)',text)
    if match:self.volume.setValue(min(100,int(float(match.group(1))*100)));self.vol_label.setText(text)
   self.command('wpctl',['get-volume','@DEFAULT_AUDIO_SINK@'],audio)
  elif self.audio=='pactl':
   def audio(text):
    match=re.search(r'(\d+)%',text)
    if match:self.volume.setValue(min(100,int(match.group(1))));self.vol_label.setText('PulseAudio/PipeWire • '+match.group(0))
   self.command('pactl',['get-sink-volume','@DEFAULT_SINK@'],audio)
  if shutil.which('brightnessctl'):
   def brightness(text):
    match=re.search(r',(\d+)%,',text)
    if match:self.brightness.setValue(int(match.group(1)));self.bri_label.setText('Brightness • '+match.group(1)+'%')
   self.command('brightnessctl',['-m','info'],brightness)
  batteries=[]
  for path in Path('/sys/class/power_supply').glob('*'):
   try:
    if (path/'type').read_text().strip()=='Battery':batteries.append(f'{path.name}: {(path/"capacity").read_text().strip()}% • {(path/"status").read_text().strip()}')
   except OSError:pass
  self.battery.setText('\n'.join(batteries) if batteries else 'Battery status is unavailable on this host.')
 def shutdown(self):
  self.closing=True;self.timer.stop()
  for process in list(self.jobs):process.kill();process.waitForFinished(500)
  return True
