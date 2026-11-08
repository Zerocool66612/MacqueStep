import time
from shiboken6 import isValid
from pathlib import Path
from PySide6.QtCore import Qt,QObject,QUrl,QTimer
from PySide6.QtMultimedia import QSoundEffect,QMediaDevices
from PySide6.QtWidgets import *
NAMES={'startup':'Startup chime','open':'Open window','close':'Close window','minimize':'Minimize window','restore':'Restore window','menu':'Open menu','click':'Button click','workspace':'Change workspace','alert':'Alert / question','error':'Error','trash':'Move to Trash','complete':'Operation complete'}
CATEGORIES={'startup':'startup','open':'windows','close':'windows','minimize':'windows','restore':'windows','menu':'menus','click':'menus','workspace':'windows','alert':'alerts','error':'alerts','trash':'alerts','complete':'alerts'}
class SoundTheme(QObject):
 def __init__(self,settings,parent=None):
  super().__init__(parent);self.settings=settings;self.effects={};self.last={};self.closed=False;self.last_error='';self.device_available=bool(QMediaDevices.audioOutputs())
 def enabled(self):return isValid(self.settings) and self.settings.value('sounds_enabled',True,type=bool)
 def volume(self):return max(0,min(1,float(self.settings.value('sounds_volume',.3))))
 def play(self,event,preview=False):
  if not isValid(self) or self.closed or event not in NAMES or not self.enabled():return False
  if not preview and not self.settings.value('sounds_'+CATEGORIES[event],True,type=bool):return False
  now=time.monotonic()
  if now-self.last.get(event,0)<(.15 if event in ('click','menu') else .08):return False
  self.last[event]=now
  if not self.device_available:self.last_error='No audio output device is available.';return False
  if event not in self.effects:
   effect=QSoundEffect(self);effect.setSource(QUrl.fromLocalFile(str(Path(__file__).with_name('assets')/'sounds'/(event+'.wav'))));effect.statusChanged.connect(lambda e=effect:self.check_status(e));self.effects[event]=effect
  effect=self.effects[event];effect.setVolume(self.volume());effect.play();return True
 def check_status(self,effect):
  if effect.status()==QSoundEffect.Error:self.last_error='The audio backend could not load or play a sound.'
 def update(self):
  for effect in self.effects.values():
   effect.setVolume(self.volume())
   if not self.enabled():effect.stop()
 def stop(self):
  for effect in self.effects.values():effect.stop()
 def shutdown(self):self.closed=True;self.stop()
class SoundPreferences(QWidget):
 def __init__(self,theme):
  super().__init__();self.theme=theme;v=QVBoxLayout(self);label=QLabel('Original retro workstation sounds • app effects volume');label.setWordWrap(True);v.addWidget(label);enabled=QCheckBox('Enable desktop sounds');enabled.setChecked(theme.enabled());enabled.toggled.connect(lambda value:self.option('sounds_enabled',value));v.addWidget(enabled);row=QHBoxLayout();row.addWidget(QLabel('Volume'));volume=QSlider(Qt.Horizontal);volume.setRange(0,100);volume.setValue(round(theme.volume()*100));volume.valueChanged.connect(lambda value:self.option('sounds_volume',value/100));row.addWidget(volume,1);v.addLayout(row)
  for title,key in [('Play startup chime','startup'),('Window and workspace sounds','windows'),('Menu and button sounds','menus'),('Alerts and file-operation sounds','alerts')]:check=QCheckBox(title);check.setChecked(theme.settings.value('sounds_'+key,True,type=bool));check.toggled.connect(lambda value,k=key:self.option('sounds_'+k,value));v.addWidget(check)
  self.items=QListWidget()
  for key,title in NAMES.items():item=QListWidgetItem(title);item.setData(Qt.UserRole,key);self.items.addItem(item)
  self.items.setCurrentRow(0);v.addWidget(self.items,1);row=QHBoxLayout();preview=QPushButton('Preview selected sound');preview.clicked.connect(self.preview);stop=QPushButton('Stop');stop.clicked.connect(theme.stop);row.addWidget(preview);row.addWidget(stop);v.addLayout(row);self.status=QLabel();self.status.setWordWrap(True);v.addWidget(self.status);self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1000);self.refresh()
 def option(self,key,value):self.theme.settings.setValue(key,value);self.theme.update();self.refresh()
 def preview(self):
  item=self.items.currentItem()
  if item:self.theme.play(item.data(Qt.UserRole),True)
  self.refresh()
 def refresh(self):self.status.setText('Muted.' if not self.theme.enabled() else self.theme.last_error or ('Ready to play on the host audio output.' if self.theme.device_available else 'No audio output device is available on this host.'))

class SoundEvents(QObject):
 def __init__(self,desktop):super().__init__(desktop);self.desktop=desktop
 def eventFilter(self,obj,event):
  from PySide6.QtCore import QEvent
  d=self.desktop
  if not isValid(d) or QApplication.closingDown() or d.exiting or not getattr(d,'_sounds_ready',False):return False
  if not isinstance(obj,QWidget) or not (obj is d or d.isAncestorOf(obj)):return False
  if event.type()==QEvent.Show:
   if isinstance(obj,QMessageBox):d.play_sound('error' if obj.icon() in (QMessageBox.Warning,QMessageBox.Critical) else 'alert')
   elif isinstance(obj,QMenu):d.play_sound('menu')
  elif event.type()==QEvent.MouseButtonRelease and isinstance(obj,QAbstractButton) and obj.isEnabled() and event.button()==Qt.LeftButton and obj.rect().contains(event.position().toPoint()):d.play_sound('click')
  return False
