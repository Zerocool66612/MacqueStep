"""Independent, live-switchable decorations for preview windows."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox,QSlider,QCheckBox
STYLES={'modern':'Modern','traffic':'Traffic lights','classic':'Classic Mac','wmaker':'Window Maker'}
def decorate(d,w):
 b=w.titlebar;style=d.settings.value('decoration_style','modern');style=style if style in STYLES else 'modern'
 controls=b.controls;l=b.controls_layout
 # Keep object creation order stable for existing minimize/maximize adapters.
 for c in controls.values():l.removeWidget(c)
 for c in controls.values():c.setStyleSheet('');c.setFixedSize(26,25)
 b.text.setAlignment(Qt.AlignLeft|Qt.AlignVCenter);b.setStyleSheet('');b.text.setStyleSheet('')
 labels={'minimize':'−','maximize':'□','close':'×'}
 if style=='traffic':
  for i,key in enumerate(('close','minimize','maximize')):
   c=controls[key];c.setText('');c.setFixedSize(16,16);color={'close':'#ff6058','minimize':'#ffbd2e','maximize':'#28c840'}[key]
   c.setStyleSheet(f'QPushButton#windowControl {{background:{color};border:1px solid #666;border-radius:8px;padding:0;}} QPushButton#windowControl:hover {{color:#222;}}');l.insertWidget(i,c)
  b.text.setAlignment(Qt.AlignCenter);b.setStyleSheet('QFrame#titlebar {background:#c8c9cc;border-bottom:1px solid #7d8085;} QLabel#titletext {color:#202126;}')
 elif style=='classic':
  b.setStyleSheet('QFrame#titlebar {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #eeeeea,stop:1 #b7b7b3);border:1px solid #333;} QLabel#titletext {color:black;background:#d9d9d5;padding:0 12px;}')
  b.text.setAlignment(Qt.AlignCenter)
  for key in ('close','minimize','maximize'):
   c=controls[key];c.setText({'close':'','minimize':'▁','maximize':'□'}[key]);c.setFixedSize(18,18);c.setStyleSheet('QPushButton#windowControl {background:#d2d2ce;border:1px solid #333;border-radius:0;padding:0;color:black;} QPushButton#windowControl:pressed {border:2px inset white;}')
  l.insertWidget(0,controls['close']);l.addWidget(controls['minimize']);l.addWidget(controls['maximize'])
 elif style=='wmaker':
  b.setStyleSheet('QFrame#titlebar {background:#77787d;border:2px outset #d9d9d9;} QLabel#titletext {color:white;font-weight:bold;}')
  for key in ('minimize','maximize','close'):
   c=controls[key];c.setText({'minimize':'▣','maximize':'□','close':'×'}[key]);c.setStyleSheet('QPushButton#windowControl {background:#b6b6b3;border:2px outset #eee;color:black;border-radius:0;padding:0;} QPushButton#windowControl:pressed {border:2px inset #eee;}')
  l.insertWidget(0,controls['minimize']);l.addWidget(controls['maximize']);l.addWidget(controls['close'])
 else:
  for key in labels:controls[key].setText(labels[key]);l.addWidget(controls[key])
 h=max(30,min(48,int(d.settings.value('titlebar_height',36))));b.setFixedHeight(h)
 for key,c in controls.items():c.setVisible(key!='maximize' or d.settings.value('decoration_zoom',True,type=bool));c.setAccessibleName(c.toolTip())
 b.setProperty('decorationStyle',style)
def apply_decorations(d):
 for w in d.windows.values():
  if hasattr(w,'titlebar'):decorate(d,w)
def decoration_preferences(d,form):
 combo=QComboBox();combo.setObjectName('decorationStyle')
 for value,label in STYLES.items():combo.addItem(label,value)
 combo.setCurrentIndex(max(0,combo.findData(d.settings.value('decoration_style','modern'))))
 def change(key,value):d.settings.setValue(key,value);apply_decorations(d)
 combo.currentIndexChanged.connect(lambda _:change('decoration_style',combo.currentData()));form.addRow('Window decorations',combo)
 height=QSlider(Qt.Horizontal);height.setRange(30,48);height.setValue(int(d.settings.value('titlebar_height',36)));height.valueChanged.connect(lambda n:change('titlebar_height',n));form.addRow('Title-bar height',height)
 zoom=QCheckBox('Show maximize / restore button');zoom.setChecked(d.settings.value('decoration_zoom',True,type=bool));zoom.toggled.connect(lambda v:change('decoration_zoom',v));form.addRow(zoom)
