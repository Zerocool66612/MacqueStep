from PySide6.QtCore import Qt,QSize
from PySide6.QtWidgets import *
from foundation import icon
from running_dock import app_kind,ICONS
class Overview(QDialog):
 def __init__(self,desktop):
  super().__init__(desktop);self.desktop=desktop;self.setWindowTitle('Workspace Overview');self.resize(900,620);root=QVBoxLayout(self);search=QLineEdit();search.setPlaceholderText('Search open windows across all four workspaces…');root.addWidget(search);grid=QGridLayout();root.addLayout(grid,1);self.lists=[]
  for n in range(4):
   group=QGroupBox(desktop.workspace_name(n));v=QVBoxLayout(group);items=QListWidget();items.setIconSize(QSize(28,28));items.setSelectionMode(QAbstractItemView.SingleSelection);v.addWidget(items);open_button=QPushButton('Switch to '+desktop.workspace_name(n));open_button.clicked.connect(lambda checked=False,i=n:self.switch(i));v.addWidget(open_button);items.itemActivated.connect(self.activate);items.setContextMenuPolicy(Qt.CustomContextMenu);items.customContextMenuRequested.connect(lambda pos,lst=items:self.context(lst,pos));grid.addWidget(group,n//2,n%2);self.lists.append(items)
  self.status=QLabel('Double-click a window to activate it. Right-click for window actions.');root.addWidget(self.status);search.textChanged.connect(self.filter);self.refresh()
 def refresh(self):
  for items in self.lists:items.clear()
  for key,w in self.desktop.windows.items():
   kind=app_kind(key)
   for n in (range(4) if w.property('sticky') else [w.property('workspace') or 0]):
    item=QListWidgetItem(icon(ICONS.get(kind,'apps')),w.windowTitle()+(' — all workspaces' if w.property('sticky') else '')+(' — shaded' if w.property('shaded') else '')+(' — minimized' if w.isMinimized() else ''));item.setData(Qt.UserRole,key);self.lists[n].addItem(item)
  self.status.setText(f'{len(self.desktop.windows)} windows across four workspaces • Double-click to activate')
 def filter(self,text):
  for items in self.lists:
   for i in range(items.count()):items.item(i).setHidden(text.lower() not in items.item(i).text().lower())
 def switch(self,n):self.desktop.switch_workspace(n);self.close()
 def activate(self,item):self.desktop.activate_running(item.data(Qt.UserRole),False);self.close()
 def context(self,items,pos):
  item=items.itemAt(pos)
  if item is None:return
  key=item.data(Qt.UserRole);menu=QMenu(self);self.desktop.running_dock.window_actions(menu,key);menu.exec(items.mapToGlobal(pos));self.refresh()
