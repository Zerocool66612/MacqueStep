import os,platform,shutil,time
from pathlib import Path
from PySide6.QtCore import Qt,QUrl,QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import *
from storage import data_root
class Extras:
 def media(self,path=None):
  if isinstance(path,bool):path=None
  if 'media' in self.windows:
   self.reopen('media')
   if path:self.windows['media'].content.load_media(path)
   return
  from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
  from PySide6.QtMultimediaWidgets import QVideoWidget
  box=QWidget();v=QVBoxLayout(box);video=QVideoWidget();video.setMinimumHeight(180);v.addWidget(video,1);status=QLabel('Open local audio or video');v.addWidget(status);seek=QSlider(Qt.Horizontal);v.addWidget(seek);row=QHBoxLayout();v.addLayout(row);player=QMediaPlayer(box);audio=QAudioOutput(box);audio.setVolume(.6);player.setAudioOutput(audio);player.setVideoOutput(video);box.player=player
  def load(p=None):
   if not p:p=QFileDialog.getOpenFileName(self,'Open media',str(Path.home()),'Media (*.mp3 *.wav *.ogg *.flac *.m4a *.mp4 *.mkv *.webm *.mov)')[0]
   if p:player.setSource(QUrl.fromLocalFile(str(p)));status.setText(Path(p).name);w.setWindowTitle(Path(p).name+' — Media Player');player.play()
  box.load_media=load
  for name,fn in [('Open',lambda:load()),('Play',player.play),('Pause',player.pause),('Stop',player.stop)]:b=QPushButton(name);b.clicked.connect(fn);row.addWidget(b)
  row.addWidget(QLabel('Volume'));volume=QSlider(Qt.Horizontal);volume.setRange(0,100);volume.setValue(60);volume.valueChanged.connect(lambda x:audio.setVolume(x/100));row.addWidget(volume)
  player.durationChanged.connect(lambda x:seek.setRange(0,x));player.positionChanged.connect(lambda x:seek.setValue(x) if not seek.isSliderDown() else None);seek.sliderReleased.connect(lambda:player.setPosition(seek.value()));player.errorOccurred.connect(lambda *args:status.setText('Playback error: '+player.errorString()));w=self.window('media','Media Player',box,(120,70,760,530))
  if path:load(path)
 def system_info(self):
  if 'system' in self.windows:self.reopen('system');return
  box=QWidget();v=QVBoxLayout(box);text=QPlainTextEdit();text.setReadOnly(True);v.addWidget(text);row=QHBoxLayout();v.addLayout(row)
  def refresh():
   usage=shutil.disk_usage(Path.home());lines=['MacaqueSTEP 0.23 — Desktop Preview','',f'Host OS: {platform.system()} {platform.release()}',f'Architecture: {platform.machine()}',f'CPU threads: {os.cpu_count()}',f'Python: {platform.python_version()}',f'Qt: {__import__("PySide6").__version__}',f'Storage: {usage.used//1024**3} GB used / {usage.total//1024**3} GB',f'Free: {usage.free//1024**3} GB',f'Session: {os.environ.get("XDG_SESSION_TYPE","unknown")}',f'Organizer data: {data_root()}']
   try:
    if Path('/proc/meminfo').exists():
     values={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()};lines.extend([f'RAM total: {values["MemTotal"]//1024} MB',f'RAM available: {values["MemAvailable"]//1024} MB'])
    if Path('/proc/uptime').exists():lines.append(f'Host uptime: {float(Path("/proc/uptime").read_text().split()[0])/3600:.1f} hours')
   except (OSError,ValueError,KeyError):pass
   text.setPlainText('\n'.join(lines))
  for title,fn in [('Refresh',refresh),('Copy report',lambda:QApplication.clipboard().setText(text.toPlainText()))]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
  refresh();self.window('system','System Information',box,(180,80,650,470))
 def clock_app(self):
  if 'clock' in self.windows:self.reopen('clock');return
  box=QWidget();v=QVBoxLayout(box);clock=QLabel();clock.setAlignment(Qt.AlignCenter);clock.setFont(QFont('monospace',28));v.addWidget(clock);display=QLabel('00:00');display.setAlignment(Qt.AlignCenter);display.setFont(QFont('monospace',36));v.addWidget(display);minutes=QSpinBox();minutes.setRange(1,1440);minutes.setValue(5);minutes.setSuffix(' minutes');v.addWidget(minutes);state={'deadline':None,'remaining':None};box.timer_state=state;row=QHBoxLayout();v.addLayout(row)
  def start():state['deadline']=time.monotonic()+(state['remaining'] if state['remaining'] is not None else minutes.value()*60);state['remaining']=None
  def pause():
   if state['deadline'] is not None:state['remaining']=max(0,state['deadline']-time.monotonic());state['deadline']=None
  def reset():state['deadline']=None;state['remaining']=None;display.setText('00:00')
  for name,fn in [('Start / Resume',start),('Pause',pause),('Reset',reset)]:b=QPushButton(name);b.clicked.connect(fn);row.addWidget(b)
  def tick():
   from datetime import datetime
   clock.setText(datetime.now().strftime('%H:%M:%S'))
   if state['deadline'] is not None:
    remaining=max(0,int(state['deadline']-time.monotonic()+.999));display.setText(f'{remaining//60:02}:{remaining%60:02}')
    if remaining==0:state['deadline']=None;state['remaining']=None;self.play_sound('complete');QMessageBox.information(self,'Timer','Your timer is finished.')
  t=QTimer(box);t.timeout.connect(tick);t.start(200);tick();self.window('clock','Clock & Timer',box,(200,100,470,330))
