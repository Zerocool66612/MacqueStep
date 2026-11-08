from PySide6.QtWidgets import *
STATUS=[
 ('Persistent left app menu','Implemented','Appears when top bar is off; active-app commands, cascading submenus and reserved workspace.'),
 ('Classic global app menus','Implemented','Active built-in app commands; focused editing, file operations, window menus and print dialogs.'),
 ('Pin and Unpin applications','Implemented','Persistent side and bottom pins; unpin retains open windows; backup support.'),
 ('Application installation','Implemented','Debian package and reversible per-user installer; full OS installer remains separate.'),
 ('Classic app icons and Window Maker gestures','Implemented','Separate icon theme; group hide/show, titlebar wheel and axis maximize.'),
 ('Workspace Clip and draggable launchers','Implemented','Workspace-specific pins; side-dock fitting; transfer/reorder between Clip, side and drawer shelf.'),
 ('Saved sessions and desktop shortcuts','Implemented','Data-only window layouts, undo, command palette; internal windows.'),
 ('POSIX/SUS technical conformance','Not verified','Host inventory only; full requirements mapping and behavioral tests remain.'),
 ('Internal desktop, docks, workspaces','Implemented','Manages MacaqueSTEP’s internal windows.'),
 ('Multi-file and folder transfers','Implemented','Staged copy, cancel, no overwrite; same-filesystem moves.'),
 ('Recursive file-name search','Implemented','Cancellable, bounded to 1,000 results.'),
 ('Installed host applications','Implemented','Discovers desktop entries; gio launches external host windows.'),
 ('Notes/tasks backup and restore','Implemented','Validated ZIP, next-launch restore, recovery database.'),
 ('Volume / brightness / battery','Host-dependent','Available only with supported utilities, devices, and permissions.'),
 ('Network / Bluetooth configuration','Host-dependent','Opens detected host settings tools.'),
 ('External window management','Not built','Needs a window manager/compositor and actual session integration.'),
 ('FreeBSD runtime port','Not verified','Requires a real FreeBSD VM and package/runtime validation.'),
 ('Live USB / installation image','Not built','Needs OS release source, image pipeline, boot and install testing.'),
 ('Installer / disk setup','Not built','Needs installer integration and recovery/partition tests.'),
 ('Updates and signed releases','Not built','Needs release hosting, signing, rollback, and update policy.'),
 ('Wi-Fi/GPU/suspend hardware validation','Not verified','Requires testing on the target desktop and laptop.'),
 ('Accessibility and full terminal compatibility','Partial','Basic labels/keyboard support; broader testing and terminal work remain.')]
class ProjectStatus(QWidget):
 def __init__(self):
  super().__init__();v=QVBoxLayout(self);label=QLabel('Desktop completion and operating-system readiness');v.addWidget(label);table=QTableWidget(len(STATUS),3);table.setHorizontalHeaderLabels(['Area','Status','Details']);table.setEditTriggers(QAbstractItemView.NoEditTriggers);table.setWordWrap(True)
  for row,values in enumerate(STATUS):
   for col,value in enumerate(values):table.setItem(row,col,QTableWidgetItem(value))
  table.setColumnWidth(0,260);table.setColumnWidth(1,130);table.horizontalHeader().setStretchLastSection(True);table.resizeRowsToContents();v.addWidget(table);v.addWidget(QLabel('Next OS milestone: select the release base, integrate the desktop session, and build a boot-tested image.'))
