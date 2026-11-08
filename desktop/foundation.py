"""Shared native desktop foundation; no versioned module dependencies."""
"""MacaqueSTEP desktop preview. No system installation or session replacement."""
import sys, os, shlex, platform
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QTimer, QProcess, QUrl
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient, QDesktopServices, QAction, QKeySequence, QIcon, QPalette
from PySide6.QtWidgets import *
THEMES = {'Dark': ('#20252b', '#30363e', '#e8edf2', '#414a55', '#15191e'), 'Light': ('#dce3e9', '#f3f5f7', '#202a34', '#bdc8d1', '#e9eef2'), 'Classic': ('#555963', '#b7b8bb', '#111318', '#777b82', '#898d95')}

class PreviewWindow(QMdiSubWindow):

    def closeEvent(self, event):
        content=getattr(self,'content',None)
        if content is not None and hasattr(content,'can_close') and not content.can_close():
            event.ignore()
            return
        edit = getattr(self.widget(), 'editor', None)
        if edit is not None and edit.document().isModified():
            if QMessageBox.question(self, 'Unsaved text', 'Discard unsaved changes?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                event.ignore()
                return
        proc = getattr(self.widget(), 'process', None)
        if proc is not None and proc.state() != QProcess.NotRunning:
            if QMessageBox.question(self, 'Running command', 'Stop this command and close?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                event.ignore()
                return
            proc.kill()
            proc.waitForFinished(1000)
        super().closeEvent(event)

class CoreDesktop(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MacaqueSTEP 0.1 — Desktop Preview')
        self.resize(1440, 900)
        self.settings = QSettings('MacaqueSTEP', 'DesktopPreview')
        self.windows = {}
        self.processes = []
        self.area = QMdiArea()
        self.area.setViewMode(QMdiArea.SubWindowView)
        self.area.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)
        root = QWidget()
        row = QHBoxLayout(root)
        row.setContentsMargins(18, 18, 18, 18)
        left = QVBoxLayout()
        brand = QLabel('◈  MacaqueSTEP')
        brand.setObjectName('brand')
        left.addWidget(brand)
        for title, fn in [('About', self.about), ('File Viewer', self.files), ('Terminal', self.terminal), ('Text Editor', self.editor), ('Preferences', self.preferences), ('Exit Preview', self.close)]:
            b = QPushButton(title)
            b.clicked.connect(fn)
            left.addWidget(b)
        left.addStretch()
        self.clock = QLabel()
        left.addWidget(self.clock)
        row.addLayout(left)
        row.addWidget(self.area, 1)
        dock = QVBoxLayout()
        dock.setSpacing(10)
        for icon, name, fn in [('◈', 'About', self.about), ('>_', 'Terminal', self.terminal), ('▤', 'Files', self.files), ('✎', 'Editor', self.editor), ('⚙', 'Preferences', self.preferences)]:
            b = QPushButton(icon)
            b.setObjectName('dock')
            b.setFixedSize(74, 74)
            b.setToolTip(name)
            b.clicked.connect(fn)
            dock.addWidget(b)
        dock.addStretch()
        row.addLayout(dock)
        self.setCentralWidget(root)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()
        self.apply_theme(self.settings.value('theme', 'Dark'))
        self.files()
        self.terminal()
        self.about()
        a = QAction(self)
        a.setShortcut(QKeySequence('F11'))
        a.triggered.connect(self.toggle_fullscreen)
        self.addAction(a)
        a = QAction(self)
        a.setShortcut(QKeySequence('Escape'))
        a.triggered.connect(self.showNormal)
        self.addAction(a)

    def tick(self):
        from datetime import datetime
        self.clock.setText(datetime.now().strftime('%a %d %b\n%H:%M'))

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def apply_theme(self, name):
        if name not in THEMES:
            name = 'Dark'
        self.theme = name
        self.settings.setValue('theme', name)
        bg, panel, fg, line, field = THEMES[name]
        self.setStyleSheet(f'QWidget {{font-family: Sans Serif; font-size: 13px; color:{fg};}} QMainWindow,QDialog {{background:{bg};}} QMdiArea {{background:{bg};}} QMdiSubWindow {{background:{panel}; border:1px solid {line};}} QPushButton {{background:{panel}; border:1px solid {line}; padding:9px; border-radius:5px;}} QPushButton:hover {{border-color:#28c9c4;}} QPushButton:pressed {{background:#1da7a4;}} QLabel#brand {{font-size:19px; font-weight:700; padding-bottom:15px;}} QPushButton#dock {{font-size:30px; border:2px solid {line}; border-radius:8px;}} QTextEdit,QPlainTextEdit,QLineEdit,QListView,QTreeView,QColumnView,QComboBox {{background:{field}; border:1px solid {line}; padding:5px; selection-background-color:#20bcb7; selection-color:#092a2b;}} QToolBar {{background:{panel}; border:0; spacing:5px;}} QMenu {{background:{panel};}} QMenu::item:selected {{background:#20bcb7;}}')
        self.area.setBackground(QColor(bg))
        pal = QApplication.palette()
        pal.setColor(QPalette.Highlight, QColor('#20bcb7'))
        pal.setColor(QPalette.HighlightedText, QColor('#092a2b'))
        QApplication.setPalette(pal)

    def window(self, key, title, widget, rect):
        if key in self.windows:
            w = self.windows[key]
            w.showNormal()
            self.area.setActiveSubWindow(w)
            return w
        w = PreviewWindow()
        w.setWidget(widget)
        self.area.addSubWindow(w)
        w.setWindowTitle(title)
        w.setAttribute(Qt.WA_DeleteOnClose)
        w.setWindowIcon(QIcon(str(Path(__file__).with_name('macaquestep.svg'))))
        w.setGeometry(*rect)
        self.windows[key] = w
        w.destroyed.connect(lambda *_: self.windows.pop(key, None))
        w.show()
        return w

    def about(self):
        box = QWidget()
        l = QVBoxLayout(box)
        h = QLabel('◈  MacaqueSTEP')
        h.setStyleSheet('font-size:30px;font-weight:700')
        l.addWidget(h)
        l.addWidget(QLabel('A classic desktop. A new beginning.\n\n0.1 • Native desktop prototype\nMade by Drew\n\nRunning on ' + platform.system() + '\nFreeBSD operating-system image is a future stage.'))
        self.window('about', 'About MacaqueSTEP', box, (190, 22, 440, 220))

    def files(self):
        from PySide6.QtWidgets import QFileSystemModel
        box = QWidget()
        l = QVBoxLayout(box)
        bar = QHBoxLayout()
        path = QLineEdit(str(Path.home()))
        go = QPushButton('Go')
        up = QPushButton('↑')
        bar.addWidget(up)
        bar.addWidget(path, 1)
        bar.addWidget(go)
        l.addLayout(bar)
        model = QFileSystemModel(box)
        model.setRootPath(str(Path.home()))
        view = QColumnView()
        view.setModel(model)
        view.setRootIndex(model.index(str(Path.home())))
        l.addWidget(view)
        note = QLabel('Browse real files • double-click a text file to edit')
        l.addWidget(note)

        def navigate():
            p = Path(path.text()).expanduser()
            if p.is_dir():
                view.setRootIndex(model.index(str(p)))
                path.setText(str(p))
            else:
                QMessageBox.warning(self, 'Location', 'That folder does not exist.')
        go.clicked.connect(navigate)
        path.returnPressed.connect(navigate)

        def parent():
            path.setText(str(Path(path.text()).parent))
            navigate()
        up.clicked.connect(parent)

        def open_file(index):
            p = Path(model.filePath(index))
            if p.is_file():
                if p.suffix.lower() in ['.txt', '.md', '.py', '.sh', '.conf', '.json', '.log', '.csv', '.ini']:
                    self.editor(p)
                elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))):
                    QMessageBox.warning(self, 'Open', 'No application could open this file.')
        view.doubleClicked.connect(open_file)
        self.window('files', 'Home — File Viewer', box, (42, 255, 760, 350))

    def editor(self, path=None):
        if isinstance(path, bool):
            path = None
        box = QWidget()
        l = QVBoxLayout(box)
        bar = QHBoxLayout()
        op = QPushButton('Open')
        save = QPushButton('Save As')
        bar.addWidget(op)
        bar.addWidget(save)
        bar.addStretch()
        l.addLayout(bar)
        edit = QPlainTextEdit()
        l.addWidget(edit)
        w = self.window('editor-' + str(id(box)), 'Text Editor', box, (160, 110, 640, 450))

        def load(p=None):
            if not p:
                p = QFileDialog.getOpenFileName(self, 'Open text file', str(Path.home()))[0]
            if p:
                try:
                    p = Path(p)
                    if p.stat().st_size > 2 * 1024 * 1024:
                        raise ValueError('Please choose a file smaller than 2 MB.')
                    edit.setPlainText(p.read_text())
                    w.setWindowTitle(p.name + ' — Text Editor')
                except (OSError, UnicodeError, ValueError) as e:
                    QMessageBox.warning(self, 'Open', str(e))

        def write():
            p = QFileDialog.getSaveFileName(self, 'Save text file', str(Path.home() / 'Untitled.txt'))[0]
            if p:
                try:
                    Path(p).write_text(edit.toPlainText())
                    edit.document().setModified(False)
                    w.setWindowTitle(Path(p).name + ' — Text Editor')
                except OSError as e:
                    QMessageBox.warning(self, 'Save', str(e))
        op.clicked.connect(lambda: load())
        save.clicked.connect(write)
        box.setProperty('editor', True)
        box.editor = edit
        if path:
            load(path)

    def terminal(self):
        if 'terminal' in self.windows:
            self.windows['terminal'].showNormal()
            self.area.setActiveSubWindow(self.windows['terminal'])
            return
        box = QWidget()
        l = QVBoxLayout(box)
        out = QPlainTextEdit()
        out.setReadOnly(True)
        out.setFont(QFont('monospace', 11))
        out.setPlainText('MacaqueSTEP command console\nCommands run on this computer. No interactive TTY.\nUse cd to change directory; Ctrl+C stops a command.\n')
        l.addWidget(out)
        cmd = QLineEdit()
        cmd.setPlaceholderText('Enter a shell command…')
        l.addWidget(cmd)
        stop = QPushButton('Stop command')
        l.addWidget(stop)
        cwd = [str(Path.home())]
        proc = QProcess(box)
        box.process = proc
        proc.setProcessChannelMode(QProcess.MergedChannels)
        self.processes.append(proc)
        proc.readyReadStandardOutput.connect(lambda: out.appendPlainText(bytes(proc.readAllStandardOutput()).decode(errors='replace')))
        proc.finished.connect(lambda *_: cmd.setEnabled(True))
        proc.errorOccurred.connect(lambda *_: (out.appendPlainText(proc.errorString()), cmd.setEnabled(True)))

        def run():
            s = cmd.text().strip()
            if not s:
                return
            out.appendPlainText(cwd[0] + ' $ ' + s)
            cmd.clear()
            if s == 'clear':
                out.clear()
                return
            if s == 'cd' or s.startswith('cd '):
                try:
                    args = shlex.split(s)
                    target = Path(os.path.expanduser(args[1] if len(args) > 1 else '~'))
                    if not target.is_absolute():
                        target = Path(cwd[0]) / target
                    target = target.resolve()
                    if not target.is_dir():
                        raise ValueError('Not a directory')
                    cwd[0] = str(target)
                except (ValueError, OSError) as e:
                    out.appendPlainText(str(e))
                return
            proc.setWorkingDirectory(cwd[0])
            proc.start('/bin/sh', ['-c', s])
            cmd.setEnabled(False)
        cmd.returnPressed.connect(run)
        stop.clicked.connect(proc.kill)
        a = QAction(box)
        a.setShortcut(QKeySequence('Ctrl+C'))
        a.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        a.triggered.connect(proc.kill)
        box.addAction(a)
        w = self.window('terminal', 'Terminal', box, (30, 625, 650, 240))
        w.destroyed.connect(lambda *_: self.processes.remove(proc) if proc in self.processes else None)

    def preferences(self):
        box = QWidget()
        l = QFormLayout(box)
        theme = QComboBox()
        theme.addItems(list(THEMES))
        theme.setCurrentText(self.theme)
        theme.currentTextChanged.connect(self.apply_theme)
        l.addRow('Appearance', theme)
        full = QPushButton('Toggle full screen (F11)')
        full.clicked.connect(self.toggle_fullscreen)
        l.addRow(full)
        l.addRow(QLabel('Escape returns to a window.\nThemes are saved automatically.\nThis preview does not replace your desktop session.'))
        self.window('preferences', 'Preferences', box, (690, 50, 340, 220))

    def closeEvent(self, event):
        modified = any((getattr(w.widget(), 'editor', None) is not None and w.widget().editor.document().isModified() for w in self.windows.values()))
        if modified and QMessageBox.question(self, 'Unsaved text', 'Discard unsaved editor changes and exit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            event.ignore()
            return
        running = [p for p in self.processes if p.state() != QProcess.NotRunning]
        if running and QMessageBox.question(self, 'Running commands', 'Stop running commands and exit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            event.ignore()
            return
        for p in running:
            p.kill()
            p.waitForFinished(1000)
        event.accept()
'MacaqueSTEP visual desktop components.'
import os, sys, json, shutil, uuid
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QSize, QPoint, QRect, QUrl
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen, QIcon, QFont, QPixmap, QDesktopServices, QAction, QKeySequence, QTextDocument
from PySide6.QtWidgets import *
ASSETS = Path(__file__).with_name('assets')

_ICON_THEME='Dark'
_ICON_CACHE={}
_ICON_NAMES={}
def set_icon_theme(theme):
    global _ICON_THEME
    _ICON_THEME=theme
def icon(name):
    style='classic' if _ICON_THEME=='Classic' else 'modern'
    key=(style,name)
    if key not in _ICON_CACHE:
        path=ASSETS/'classic'/(name+'.svg') if style=='classic' else ASSETS/(name+'.svg')
        if not path.exists():path=ASSETS/(name+'.svg')
        value=QIcon(str(path));_ICON_CACHE[key]=value;_ICON_NAMES[value.cacheKey()]=name
    return _ICON_CACHE[key]
def refresh_icon_widgets(root):
    for widget in root.findChildren(QAbstractButton):
        name=_ICON_NAMES.get(widget.icon().cacheKey())
        if name:widget.setIcon(icon(name))
    for action in root.findChildren(QAction):
        name=_ICON_NAMES.get(action.icon().cacheKey())
        if name:action.setIcon(icon(name))

class Wallpaper(QMdiArea):

    def __init__(self):
        super().__init__()
        self.theme = 'Dark'
        self.pattern = 'Geometry'

    def paintEvent(self, e):
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.Antialiasing)
        light = self.theme == 'Light'
        classic = self.theme == 'Classic'
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor('#eaf0f4' if light else '#535762' if classic else '#303d4a'))
        g.setColorAt(1, QColor('#bccbd7' if light else '#656975' if classic else '#121b25'))
        p.fillRect(self.viewport().rect(), g)
        if self.pattern == 'Geometry':
            p.setPen(Qt.NoPen)
            for i in range(5):
                p.setBrush(QColor(255, 255, 255, 15 if light else 5))
                x = self.width() * (0.23 + i * 0.25)
                p.drawPolygon([QPoint(int(x), 0), QPoint(int(x + 200), 0), QPoint(int(x - 300), self.height()), QPoint(int(x - 500), self.height())])
        p.setOpacity(0.08 if light else 0.045)
        pix = icon('monkey').pixmap(300, 300)
        p.drawPixmap(self.width() - 340, self.height() - 360, pix)
        p.setOpacity(1)
        p.setPen(QColor('#748693' if light else '#718393'))
        p.setFont(QFont('Sans Serif', 10))

class TitleBar(QFrame):

    def __init__(self, w, title, kind):
        super().__init__()
        self.w = w
        self.offset = None
        self.setObjectName('titlebar')
        self.setFixedHeight(36)
        l = QHBoxLayout(self)
        self.controls_layout = l
        self.controls = {}
        l.setContentsMargins(10, 0, 6, 0)
        pic = QLabel()
        pic.setPixmap(icon(kind).pixmap(20, 20))
        l.addWidget(pic)
        self.text = QLabel(title)
        self.text.setObjectName('titletext')
        l.addWidget(self.text, 1)
        for label, tip, fn in [('−', 'Minimize', w.showMinimized), ('□', 'Maximize / restore', self.maximize), ('×', 'Close', w.close)]:
            b = QPushButton(label)
            b.setToolTip(tip)
            b.setFixedSize(26, 25)
            b.setObjectName('windowControl')
            b.clicked.connect(fn)
            self.controls[tip.split(' ')[0].lower()] = b
            l.addWidget(b)

    def paintEvent(self,event):
        super().paintEvent(event)
        if self.property('decorationStyle') == 'classic':
            painter=QPainter(self);painter.setPen(QColor('#777772'))
            for y in range(8,self.height()-6,4):painter.drawLine(34,y,self.width()-58,y)
            painter.end()

    def maximize(self):
        self.w.showNormal() if self.w.isMaximized() else self.w.showMaximized()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.offset = e.globalPosition().toPoint() - self.w.pos()

    def mouseMoveEvent(self, e):
        if self.offset is not None and (not self.w.isMaximized()):
            self.w.move(e.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, e):
        self.offset = None

    def mouseDoubleClickEvent(self, e):
        self.maximize()

class VisualDesktop(CoreDesktop):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('MacaqueSTEP 0.2 — Desktop Preview')
        self.resize(1460, 930)
        self.setMinimumSize(800, 600)
        from PySide6.QtCore import QSettings
        self.settings = QSettings('MacaqueSTEP', 'DesktopPreview')
        self.windows = {}
        self.processes = []
        self.theme = self.settings.value('theme', 'Dark')
        self.dock_buttons = {}
        self.area = Wallpaper()
        self.area.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)
        root = QWidget()
        root.setObjectName('shell')
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        top = QFrame()
        top.setObjectName('topbar')
        t = QHBoxLayout(top)
        t.setContentsMargins(14, 5, 14, 5)
        menu = QPushButton('◈  MacaqueSTEP')
        m = QMenu(menu)
        for name, fn in [('About MacaqueSTEP', self.about), ('Applications', self.launcher), ('Preferences', self.preferences), ('Restore window layout', self.reset_layout), ('Exit Preview', self.close)]:
            m.addAction(name, fn)
        menu.setMenu(m)
        t.addWidget(menu)
        caption = QLabel('Desktop Preview')
        caption.setObjectName('muted')
        t.addWidget(caption)
        t.addStretch()
        self.clock = QLabel()
        t.addWidget(self.clock)
        layout.addWidget(top)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 12, 0)
        body.addWidget(self.area, 1)
        dock = QVBoxLayout()
        dock.setSpacing(9)
        dock.addSpacing(20)
        for key, label, fn in [('monkey', 'About MacaqueSTEP', self.about), ('files', 'File Viewer', self.files), ('terminal', 'Terminal', self.terminal), ('editor', 'Text Editor', self.editor), ('apps', 'Applications', self.launcher), ('camera', 'Screenshot', self.screenshot), ('settings', 'Preferences', self.preferences)]:
            b = QPushButton()
            b.setObjectName('dock')
            b.setIcon(icon(key))
            b.setIconSize(QSize(43, 43))
            b.setFixedSize(68, 68)
            b.setToolTip(label)
            b.clicked.connect(fn)
            dock.addWidget(b)
            self.dock_buttons[key] = b
        dock.addStretch()
        body.addLayout(dock)
        layout.addLayout(body, 1)
        self.setCentralWidget(root)
        self.area.setContextMenuPolicy(Qt.CustomContextMenu)
        self.area.customContextMenuRequested.connect(self.desktop_menu)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()
        self.apply_theme(self.theme)
        for keys, fn in [('F11', self.toggle_fullscreen), ('Escape', self.showNormal), ('Ctrl+Alt+T', self.terminal), ('Ctrl+Space', self.launcher)]:
            a = QAction(self)
            a.setShortcut(QKeySequence(keys))
            a.triggered.connect(fn)
            self.addAction(a)
        QTimer.singleShot(100, self.startup)

    def startup(self):
        self.files()
        self.terminal()
        self.about()
        self.reset_layout()

    def tick(self):
        from datetime import datetime
        self.clock.setText(datetime.now().strftime('%a %d %b  •  %H:%M'))

    def apply_theme(self, name):
        CoreDesktop.apply_theme(self, name)
        self.area.theme = self.theme
        self.area.pattern = self.settings.value('wallpaper', 'Geometry')
        self.area.viewport().update()
        bg, panel, fg, line, field = THEMES[self.theme]
        self.setStyleSheet(self.styleSheet() + f"\n  QWidget#shell {{background:{bg};}} QFrame#topbar {{background:{panel};border-bottom:1px solid {line};}}\n  QFrame#titlebar {{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #38434f,stop:1 #202a34);border-bottom:1px solid #121a23;}}\n  QLabel#titletext {{color:#f2f5f7;font-weight:600;}}\n  QPushButton#windowControl {{background:#344451;color:#e2eef5;border:1px solid #556775;padding:0;border-radius:3px;font-size:18px;}}\n  QPushButton#dock {{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {panel},stop:1 {bg});border:1px solid {line};border-top:1px solid #91a0ac;border-radius:7px;padding:7px;}}\n  QPushButton#dock:hover {{background:{line};border:1px solid #2cc9bd;}}\n  QLabel#muted {{color:{('#667b89' if self.theme == 'Light' else '#9baebb')};font-size:12px;}}\n  QFrame#windowBody {{background:{panel};border:1px solid {line};border-radius:5px;}}\n  QScrollBar:vertical {{width:10px;background:{field};}} QScrollBar::handle:vertical {{background:{line};min-height:20px;}}\n  QListWidget::item {{padding:8px;}} QListWidget::item:selected {{background:#26bdb5;color:#092c31;}}\n  ")
        for w in self.windows.values():
            if hasattr(w, 'titlebar'):
                w.titlebar.update()

    def window(self, key, title, widget, rect):
        if key in self.windows:
            widget.deleteLater()
            w = self.windows[key]
            w.showNormal()
            w.raise_()
            self.area.setActiveSubWindow(w)
            self.ensure_visible(w)
            return w
        w = PreviewWindow()
        w.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
        w.setWindowTitle(title)
        w.setAttribute(Qt.WA_DeleteOnClose)
        frame = QFrame()
        frame.setObjectName('windowBody')
        l = QVBoxLayout(frame)
        l.setContentsMargins(1, 1, 1, 1)
        l.setSpacing(0)
        kind = 'files' if key == 'files' else 'terminal' if key == 'terminal' else 'editor' if key.startswith('editor') else 'settings' if key == 'preferences' else 'apps' if key == 'launcher' else 'monkey'
        bar = TitleBar(w, title, kind)
        w.titlebar = bar
        l.addWidget(bar)
        l.addWidget(widget, 1)
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.addStretch()
        bottom.addWidget(QSizeGrip(frame))
        l.addLayout(bottom)
        w.setWidget(frame)
        w.content = widget
        self.area.addSubWindow(w)
        w.setMinimumSize(300, 160)
        w.setGeometry(*rect)
        self.windows[key] = w
        w.windowTitleChanged.connect(bar.text.setText)
        w.destroyed.connect(lambda *_: self.windows.pop(key, None))
        w.show()
        self.ensure_visible(w)
        if hasattr(widget, 'process'):
            frame.process = widget.process
        return w

    def ensure_visible(self, w):
        r = self.area.viewport().rect()
        w.resize(min(w.width(), max(300, r.width() - 20)), min(w.height(), max(160, r.height() - 20)))
        w.move(max(0, min(w.x(), r.width() - w.width())), max(0, min(w.y(), r.height() - w.height())))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'windows'):
            for w in self.windows.values():
                if not w.isMinimized() and (not w.isMaximized()):
                    self.ensure_visible(w)

    def reset_layout(self):
        r = self.area.viewport().rect()
        width = r.width()
        height = r.height()
        positions = {'files': (35, int(height * 0.28), int(width * 0.72), int(height * 0.4)), 'terminal': (35, int(height * 0.7), int(width * 0.55), int(height * 0.3) - 10), 'about': (int(width * 0.35), 25, min(470, int(width * 0.6)), 190)}
        for key, rect in positions.items():
            if key in self.windows:
                w = self.windows[key]
                w.showNormal()
                w.setGeometry(*rect)
                self.ensure_visible(w)

    def desktop_menu(self, pos):
        m = QMenu(self)
        for label, fn in [('Applications', self.launcher), ('New text document', self.editor), ('Terminal', self.terminal), ('Preferences', self.preferences), ('Restore window layout', self.reset_layout)]:
            m.addAction(label, fn)
        m.exec(self.area.mapToGlobal(pos))

    def about(self):
        box = QWidget()
        l = QHBoxLayout(box)
        p = QLabel()
        p.setPixmap(icon('monkey').pixmap(92, 92))
        l.addWidget(p)
        v = QVBoxLayout()
        h = QLabel('MacaqueSTEP')
        h.setStyleSheet('font-size:28px;font-weight:700')
        v.addWidget(h)
        v.addWidget(QLabel('A classic desktop. A new beginning.'))
        s = QLabel('0.2 • Desktop preview\nMade by Drew')
        s.setObjectName('muted')
        v.addWidget(s)
        l.addLayout(v)
        self.window('about', 'About MacaqueSTEP', box, (350, 35, 470, 190))

    def terminal(self):
        CoreDesktop.terminal(self)
        if 'terminal' in self.windows:
            w = self.windows['terminal']
            self.ensure_visible(w)
            if hasattr(w, 'content'):
                out = w.content.findChild(QPlainTextEdit)
                if out:
                    out.setMaximumBlockCount(10000)

    def preferences(self):
        box = QWidget()
        l = QFormLayout(box)
        theme = QComboBox()
        theme.addItems(THEMES)
        theme.setCurrentText(self.theme)
        theme.currentTextChanged.connect(self.apply_theme)
        l.addRow('Appearance', theme)
        wall = QComboBox()
        wall.addItems(['Geometry', 'Gradient'])
        wall.setCurrentText(self.settings.value('wallpaper', 'Geometry'))

        def wallpaper(s):
            self.settings.setValue('wallpaper', s)
            self.area.pattern = s
            self.area.viewport().update()
        wall.currentTextChanged.connect(wallpaper)
        l.addRow('Wallpaper', wall)
        for title, fn in [('Restore window layout', self.reset_layout), ('Full screen • F11', self.toggle_fullscreen), ('Save screenshot…', self.screenshot)]:
            b = QPushButton(title)
            b.clicked.connect(fn)
            l.addRow(b)
        l.addRow(QLabel('Ctrl+Space  Applications\nCtrl+Alt+T  Terminal\nEscape  Leave full screen'))
        self.window('preferences', 'Preferences', box, (650, 120, 360, 340))

    def screenshot(self):
        p = QFileDialog.getSaveFileName(self, 'Save desktop screenshot', str(Path.home() / 'MacaqueSTEP-desktop.png'), 'PNG image (*.png)')[0]
        if p and (not self.grab().save(p, 'PNG')):
            QMessageBox.warning(self, 'Screenshot', 'Could not save the image.')

    def files(self):
        if 'files' in self.windows:
            w = self.windows['files']
            w.showNormal()
            w.raise_()
            self.ensure_visible(w)
            return
        box = QWidget()
        l = QVBoxLayout(box)
        bar = QHBoxLayout()
        up = QPushButton('↑')
        up.setFixedWidth(38)
        location = QLineEdit(str(Path.home()))
        go = QPushButton('Go')
        bar.addWidget(up)
        bar.addWidget(location, 1)
        bar.addWidget(go)
        l.addLayout(bar)
        split = QSplitter()
        side = QListWidget()
        side.setMaximumWidth(180)
        side.setMinimumWidth(160)
        side.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        places = [('Home', Path.home()), ('Documents', Path.home() / 'Documents'), ('Downloads', Path.home() / 'Downloads'), ('Pictures', Path.home() / 'Pictures'), ('Filesystem', Path('/'))]
        for name, p in places:
            side.addItem(QListWidgetItem(icon('files'), name))
        model = QFileSystemModel(box)
        model.setRootPath(str(Path.home()))
        view = QColumnView()
        view.setModel(model)
        view.setColumnWidths([190, 190, 190])
        split.addWidget(side)
        split.addWidget(view)
        split.setStretchFactor(1, 1)
        l.addWidget(split, 1)
        bottom = QHBoxLayout()
        status = QLabel()
        status.setObjectName('muted')
        bottom.addWidget(status, 1)
        new = QPushButton('New folder')
        hidden = QCheckBox('Hidden files')
        bottom.addWidget(hidden)
        bottom.addWidget(new)
        l.addLayout(bottom)
        from PySide6.QtCore import QDir

        def navigate(target=None):
            p = Path(target or location.text()).expanduser()
            if p.is_dir():
                p = p.resolve()
                location.setText(str(p))
                view.setRootIndex(model.index(str(p)))
                try:
                    usage = shutil.disk_usage(p)
                    status.setText(f'{usage.free // 1024 ** 3} GB available • Double-click to open')
                except OSError:
                    status.setText('Double-click to open')
            else:
                QMessageBox.warning(self, 'Folder', 'This folder is unavailable.')
        go.clicked.connect(lambda: navigate())
        location.returnPressed.connect(lambda: navigate())
        up.clicked.connect(lambda: navigate(Path(location.text()).parent))
        side.currentRowChanged.connect(lambda i: navigate(places[i][1]) if i >= 0 else None)
        hidden.toggled.connect(lambda checked: model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | (QDir.Hidden if checked else QDir.Filter(0))))

        def mkdir():
            name, ok = QInputDialog.getText(self, 'New folder', 'Folder name')
            if ok and name:
                if name in ('.', '..') or '/' in name:
                    QMessageBox.warning(self, 'Folder', 'Enter a single folder name.')
                    return
                try:
                    (Path(location.text()) / name).mkdir()
                except OSError as e:
                    QMessageBox.warning(self, 'Folder', str(e))
        new.clicked.connect(mkdir)

        def open_file(index):
            p = Path(model.filePath(index))
            if p.is_file():
                if p.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'] and hasattr(self, 'images'):
                    self.images(p)
                elif p.suffix.lower() in ['.txt', '.md', '.py', '.sh', '.conf', '.json', '.log', '.csv', '.ini', '.svg', '.desktop', '.yaml', '.yml']:
                    self.editor(p)
                elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))):
                    QMessageBox.warning(self, 'Open', 'No application could open the file.')
        view.doubleClicked.connect(open_file)
        navigate(Path.home())
        self.window('files', 'Home — File Viewer', box, (35, 230, 840, 400))

    def editor(self, path=None):
        if isinstance(path, bool):
            path = None
        box = QWidget()
        l = QVBoxLayout(box)
        bar = QHBoxLayout()
        edit = QPlainTextEdit()
        edit.setFont(QFont('monospace', 12))
        box.editor = edit
        current = [None]
        status = QLabel('Ready')
        search = QLineEdit()
        search.setPlaceholderText('Find text…')
        search.setMaximumWidth(170)

        def discard():
            return not edit.document().isModified() or QMessageBox.question(self, 'Unsaved text', 'Discard unsaved changes?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes

        def load(p=None):
            if not discard():
                return
            if not p:
                p = QFileDialog.getOpenFileName(self, 'Open text file', str(Path.home()))[0]
            if not p:
                return
            try:
                p = Path(p)
                if p.stat().st_size > 2 * 1024 * 1024:
                    raise ValueError('Choose a text file smaller than 2 MB.')
                text = p.read_text()
                edit.setPlainText(text)
                edit.document().setModified(False)
                current[0] = p
                w.setWindowTitle(p.name + ' — Text Editor')
            except (OSError, UnicodeError, ValueError) as e:
                QMessageBox.warning(self, 'Open', str(e))

        def save(as_new=False):
            p = current[0]
            if p is None or as_new:
                name = QFileDialog.getSaveFileName(self, 'Save text file', str(p or Path.home() / 'Untitled.txt'))[0]
                if not name:
                    return
                p = Path(name)
            try:
                from PySide6.QtCore import QSaveFile, QIODevice
                f = QSaveFile(str(p))
                if not f.open(QIODevice.WriteOnly):
                    raise OSError(f.errorString())
                data = edit.toPlainText().encode('utf-8')
                if f.write(data) != len(data) or not f.commit():
                    raise OSError(f.errorString())
                current[0] = p
                edit.document().setModified(False)
                w.setWindowTitle(p.name + ' — Text Editor')
                status.setText('Saved ' + p.name)
            except OSError as e:
                QMessageBox.warning(self, 'Save', str(e))
        for name, fn in [('Open', lambda: load()), ('Save', lambda: save()), ('Save As', lambda: save(True))]:
            b = QPushButton(name)
            b.clicked.connect(fn)
            bar.addWidget(b)
        bar.addStretch()
        bar.addWidget(search)
        l.addLayout(bar)
        l.addWidget(edit, 1)
        l.addWidget(status)
        w = self.window('editor-' + uuid.uuid4().hex, 'Untitled — Text Editor', box, (150, 100, 700, 480))
        w.widget().editor = edit

        def find():
            if not edit.find(search.text()):
                cursor = edit.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                edit.setTextCursor(cursor)
                edit.find(search.text())
        box.menu_commands={'open':lambda:load(),'save':lambda:save(),'save_as':lambda:save(True),'find':search.setFocus,'find_next':find}
        search.returnPressed.connect(find)
        edit.cursorPositionChanged.connect(lambda: status.setText(f'Line {edit.textCursor().blockNumber() + 1}  •  Column {edit.textCursor().columnNumber() + 1}'))
        edit.modificationChanged.connect(lambda dirty: w.setWindowTitle(('* ' if dirty else '') + (current[0].name if current[0] else 'Untitled') + ' — Text Editor'))
        for keys, fn in [('Ctrl+S', lambda: save()), ('Ctrl+O', lambda: load()), ('Ctrl+Shift+S',lambda:save(True)), ('Ctrl+F', search.setFocus)]:
            a = QAction(box)
            a.setShortcut(QKeySequence(keys))
            a.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            a.triggered.connect(fn)
            box.addAction(a)
        if path:
            load(path)
        return w

    def launcher(self):
        box = QWidget()
        l = QVBoxLayout(box)
        search = QLineEdit()
        search.setPlaceholderText('Search applications…')
        l.addWidget(search)
        items = QListWidget()
        l.addWidget(items)
        entries = [('File Viewer', 'files', self.files), ('Terminal', 'terminal', self.terminal), ('Text Editor', 'editor', self.editor), ('Preferences', 'settings', self.preferences), ('Screenshot', 'camera', self.screenshot), ('About MacaqueSTEP', 'monkey', self.about)]
        for title, kind, fn in entries:
            items.addItem(QListWidgetItem(icon(kind), title))

        def filter_items(text):
            for i in range(items.count()):
                items.item(i).setHidden(text.lower() not in items.item(i).text().lower())
        search.textChanged.connect(filter_items)
        items.itemActivated.connect(lambda item: entries[items.row(item)][2]())
        w = self.window('launcher', 'Applications', box, (190, 80, 410, 450))
        search.setFocus()
'MacaqueSTEP built-in tools.'
import sys, os, json, ast, operator, math, uuid
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QSize, QEvent, QObject, QProcess, QSettings, QUrl
from PySide6.QtGui import QFont, QPixmap, QImageReader, QAction, QKeySequence, QDesktopServices
from PySide6.QtWidgets import *
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Mod: operator.mod}

def calculate(source):
    if len(source) > 250:
        raise ValueError('Expression is too long')

    def visit(n, depth=0):
        if depth > 20:
            raise ValueError('Expression is too complex')
        if isinstance(n, ast.Constant) and type(n.value) in (float, int):
            value = n.value
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            value = (-1 if isinstance(n.op, ast.USub) else 1) * visit(n.operand, depth + 1)
        elif isinstance(n, ast.BinOp) and type(n.op) in OPS:
            value = OPS[type(n.op)](visit(n.left, depth + 1), visit(n.right, depth + 1))
        else:
            raise ValueError('Use numbers, parentheses, +, −, *, /, or %')
        if not math.isfinite(value) or abs(value) > 1e+100:
            raise ValueError('Result is too large')
        return value
    return visit(ast.parse(source, mode='eval').body)

class HistoryLine(QLineEdit):

    def __init__(self):
        super().__init__()
        self.history = []
        self.index = 0

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Up, Qt.Key_Down):
            self.index = max(0, min(len(self.history), self.index + (-1 if e.key() == Qt.Key_Up else 1)))
            self.setText(self.history[self.index] if self.index < len(self.history) else '')
            return
        super().keyPressEvent(e)

    def remember(self, s):
        if not self.history or self.history[-1] != s:
            self.history.append(s)
        self.history = self.history[-200:]
        self.index = len(self.history)

class ToolDesktop(VisualDesktop):

    def __init__(self):
        self.restoring = False
        super().__init__()
        self.setWindowTitle('MacaqueSTEP 0.3 — Desktop Preview')
        self.add_dock('calculator', 'Calculator', self.calculator, 'calculator')
        self.add_dock('images', 'Image Viewer', self.images, 'image')
        self.add_dock('windows', 'Open Windows', self.window_list, 'windows')
        self.apply_dock_size(int(self.settings.value('dock_size', 54)))
        self.area.subWindowActivated.connect(self.update_tasks)
        a = QAction(self)
        a.setShortcut(QKeySequence('Ctrl+Tab'))
        a.triggered.connect(self.area.activateNextSubWindow)
        self.addAction(a)
        a = QAction(self)
        a.setShortcut(QKeySequence('Ctrl+Alt+W'))
        a.triggered.connect(self.window_list)
        self.addAction(a)

    def add_dock(self, key, title, fn, kind):
        b = QPushButton()
        b.setObjectName('dock')
        b.setIcon(icon(kind))
        b.setToolTip(title)
        b.clicked.connect(fn)
        body = self.centralWidget().layout().itemAt(1).layout()
        dock = body.itemAt(1).layout()
        dock.insertWidget(dock.count() - 1, b)
        self.dock_buttons[key] = b

    def apply_dock_size(self, size):
        size = max(24, min(68, size))
        self.settings.setValue('dock_size', size)
        for b in self.dock_buttons.values():
            b.setFixedSize(size, size)
            b.setIconSize(QSize(max(22, size - 20), max(22, size - 20)))
        dock = self.centralWidget().layout().itemAt(1).layout().itemAt(1).layout()
        dock.setSpacing(5)

    def window(self, key, title, widget, rect):
        existed = key in self.windows
        w = super().window(key, title, widget, rect)
        if not existed:
            w.destroyed.connect(lambda *_: QTimer.singleShot(0, self.update_tasks))
        QTimer.singleShot(0, self.update_tasks)
        return w

    def startup(self):
        self.files()
        self.terminal()
        self.about()
        self.reset_layout()
        if self.settings.value('restore_layout', True, type=bool):
            try:
                layouts = json.loads(self.settings.value('layouts_v3', '{}'))
            except (ValueError, TypeError):
                layouts = {}
            for key, rect in layouts.items():
                if key in self.windows and isinstance(rect, list) and (len(rect) == 4) and all((type(v) == int for v in rect)):
                    self.windows[key].setGeometry(*rect)
                    self.ensure_visible(self.windows[key])

    def update_tasks(self, *_):
        if 'window-list' not in self.windows:
            return
        content = self.windows['window-list'].content
        items = content.findChild(QListWidget)
        if items is None:
            return
        items.clear()
        for key, w in self.windows.items():
            if key == 'window-list':
                continue
            item = QListWidgetItem(('▁  ' if w.isMinimized() else '') + w.windowTitle())
            item.setData(Qt.UserRole, key)
            items.addItem(item)

    def window_list(self):
        box = QWidget()
        l = QVBoxLayout(box)
        items = QListWidget()
        l.addWidget(items)

        def activate(item):
            key = item.data(Qt.UserRole)
            if key in self.windows:
                w = self.windows[key]
                w.showNormal()
                w.raise_()
                self.area.setActiveSubWindow(w)
                self.ensure_visible(w)
        items.itemActivated.connect(activate)
        row = QHBoxLayout()
        for label, fn in [('Tile', self.area.tileSubWindows), ('Cascade', self.area.cascadeSubWindows), ('Restore layout', self.reset_layout)]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            row.addWidget(b)
        l.addLayout(row)
        self.window('window-list', 'Open Windows', box, (220, 90, 440, 420))
        self.update_tasks()

    def calculator(self):
        box = QWidget()
        l = QVBoxLayout(box)
        entry = QLineEdit()
        entry.setAlignment(Qt.AlignRight)
        entry.setFont(QFont('monospace', 20))
        entry.setPlaceholderText('0')
        l.addWidget(entry)
        result = QLabel('Enter an expression')
        result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        l.addWidget(result)

        def solve():
            try:
                value = calculate(entry.text())
                result.setText(str(value))
                entry.setText(str(value))
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as e:
                result.setText(str(e))
        grid = QGridLayout()
        for i, label in enumerate(['7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '0', '.', '(', ')']):
            b = QPushButton(label)
            b.setMinimumHeight(36)
            b.clicked.connect(lambda checked=False, s=label: entry.insert(s))
            grid.addWidget(b, i // 4, i % 4)
        l.addLayout(grid)
        row = QHBoxLayout()
        for label, fn in [('Clear', entry.clear), ('+', lambda: entry.insert('+')), ('=', solve), ('Copy', lambda: QApplication.clipboard().setText(result.text()))]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            row.addWidget(b)
        l.addLayout(row)
        entry.returnPressed.connect(solve)
        self.window('calculator', 'Calculator', box, (220, 90, 360, 400))

    def images(self, path=None):
        if isinstance(path, bool):
            path = None
        box = QWidget()
        l = QVBoxLayout(box)
        bar = QHBoxLayout()
        label = QLabel('Open an image to begin')
        label.setAlignment(Qt.AlignCenter)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(label)
        pix = [None]
        zoom = [1.0]
        status = QLabel('PNG • JPEG • WebP • BMP • GIF (first frame)')

        def render():
            if pix[0] is None:
                return
            zoom[0] = min(zoom[0], math.sqrt(32000000 / (pix[0].width() * pix[0].height())))
            size = pix[0].size() * zoom[0]
            scaled = pix[0].scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
            label.setMinimumSize(scaled.size())
            status.setText(f'{pix[0].width()} × {pix[0].height()}  •  {round(zoom[0] * 100)}%')

        def load(p=None):
            if not p:
                p = QFileDialog.getOpenFileName(self, 'Open image', str(Path.home()), 'Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)')[0]
            if not p:
                return
            reader = QImageReader(str(p))
            reader.setAutoTransform(True)
            size = reader.size()
            if size.isValid() and size.width() * size.height() > 60000000:
                QMessageBox.warning(self, 'Image', 'Please choose an image under 60 megapixels.')
                return
            img = reader.read()
            if img.isNull():
                QMessageBox.warning(self, 'Image', reader.errorString())
                return
            pix[0] = QPixmap.fromImage(img)
            zoom[0] = min(1.0, 640 / pix[0].width(), 420 / pix[0].height())
            render()
            w.setWindowTitle(Path(p).name + ' — Image Viewer')

        def scale(f):
            zoom[0] = max(0.05, min(4, zoom[0] * f))
            render()

        def fit():
            if pix[0] is not None:
                zoom[0] = min(scroll.viewport().width() / pix[0].width(), scroll.viewport().height() / pix[0].height())
                render()
        for name, fn in [('Open', lambda: load()), ('−', lambda: scale(0.8)), ('+', lambda: scale(1.25)), ('Fit', fit), ('100%', lambda: (zoom.__setitem__(0, 1), render()))]:
            b = QPushButton(name)
            b.clicked.connect(fn)
            bar.addWidget(b)
        l.addLayout(bar)
        l.addWidget(scroll, 1)
        l.addWidget(status)
        w = self.window('image-' + uuid.uuid4().hex, 'Image Viewer', box, (120, 80, 760, 560))
        if path:
            load(path)
        return w

    def terminal(self):
        if 'terminal' in self.windows:
            w = self.windows['terminal']
            w.showNormal()
            w.raise_()
            self.ensure_visible(w)
            return
        box = QWidget()
        l = QVBoxLayout(box)
        out = QPlainTextEdit()
        out.setReadOnly(True)
        out.setFont(QFont('monospace', 11))
        out.setMaximumBlockCount(10000)
        out.setPlainText('MacaqueSTEP 0.5 command console\nUp / Down: history • cd: change folder • clear: clear output\nCommands run on this computer. Interactive TTY apps are unsupported.\n')
        l.addWidget(out, 1)
        cwd = [str(Path.home())]
        prompt = QLabel(cwd[0])
        l.addWidget(prompt)
        row = QHBoxLayout()
        cmd = HistoryLine()
        cmd.setPlaceholderText('Enter a shell command…')
        stop = QPushButton('Stop')
        row.addWidget(cmd, 1)
        row.addWidget(stop)
        l.addLayout(row)
        proc = QProcess(box)
        box.process = proc
        self.processes.append(proc)
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: out.appendPlainText(bytes(proc.readAllStandardOutput()).decode(errors='replace')))

        def finished(code, *_):
            cmd.setEnabled(True)
            cmd.setFocus()
            prompt.setText(cwd[0] + f'  •  exit {code}')
        proc.finished.connect(finished)
        proc.errorOccurred.connect(lambda *_: (out.appendPlainText(proc.errorString()), cmd.setEnabled(True)))

        def run():
            import shlex
            s = cmd.text().strip()
            if not s:
                return
            cmd.remember(s)
            cmd.clear()
            out.appendPlainText(cwd[0] + ' $ ' + s)
            if s == 'clear':
                out.clear()
                return
            if s == 'cd' or s.startswith('cd '):
                try:
                    args = shlex.split(s)
                    if len(args) > 2:
                        raise ValueError('Quote folder names containing spaces.')
                    p = Path(os.path.expanduser(args[1] if len(args) > 1 else '~'))
                    if not p.is_absolute():
                        p = Path(cwd[0]) / p
                    p = p.resolve()
                    if not p.is_dir():
                        raise ValueError('Folder does not exist')
                    cwd[0] = str(p)
                    prompt.setText(cwd[0])
                except (ValueError, OSError) as e:
                    out.appendPlainText(str(e))
                return
            proc.setWorkingDirectory(cwd[0])
            proc.start('/bin/sh', ['-c', s])
            cmd.setEnabled(False)
        cmd.returnPressed.connect(run)
        stop.clicked.connect(proc.kill)
        a = QAction(box)
        a.setShortcut(QKeySequence('Ctrl+C'))
        a.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        a.triggered.connect(proc.kill)
        box.addAction(a)
        w = self.window('terminal', 'Terminal', box, (35, 530, 740, 270))
        w.destroyed.connect(lambda *_: self.processes.remove(proc) if proc in self.processes else None)

    def preferences(self):
        if 'preferences' in self.windows:
            w = self.windows['preferences']
            w.showNormal()
            w.raise_()
            return
        super().preferences()
        box = self.windows['preferences'].content
        l = box.layout()
        size = QSlider(Qt.Horizontal)
        size.setRange(24, 68)
        size.setValue(int(self.settings.value('dock_size', 54)))
        size.valueChanged.connect(self.apply_dock_size)
        size.setObjectName('dockSizeSlider');l.addRow('Dock tile size', size)
        restore = QCheckBox('Restore window positions on startup')
        restore.setChecked(self.settings.value('restore_layout', True, type=bool))
        restore.toggled.connect(lambda v: self.settings.setValue('restore_layout', v))
        l.addRow(restore)
        b = QPushButton('Open Windows • Ctrl+Alt+W')
        b.clicked.connect(self.window_list)
        l.addRow(b)
        self.windows['preferences'].resize(410, 450)
        self.ensure_visible(self.windows['preferences'])

    def about(self):
        super().about()
        for label in self.windows['about'].content.findChildren(QLabel):
            if '0.2' in label.text():
                label.setText(label.text().replace('0.2', '0.3'))

    def launcher(self):
        if 'launcher' in self.windows:
            w = self.windows['launcher']
            w.showNormal()
            w.raise_()
            return
        box = QWidget()
        l = QVBoxLayout(box)
        search = QLineEdit()
        search.setPlaceholderText('Search applications…')
        items = QListWidget()
        l.addWidget(search)
        l.addWidget(items)
        entries = [('File Viewer', 'files', self.files), ('Terminal', 'terminal', self.terminal), ('Text Editor', 'editor', self.editor), ('Image Viewer', 'image', self.images), ('Calculator', 'calculator', self.calculator), ('Preferences', 'settings', self.preferences), ('Screenshot', 'camera', self.screenshot), ('Open Windows', 'windows', self.window_list), ('About MacaqueSTEP', 'monkey', self.about)]
        for name, kind, fn in entries:
            items.addItem(QListWidgetItem(icon(kind), name))

        def filter_items(s):
            for i in range(items.count()):
                items.item(i).setHidden(s.lower() not in items.item(i).text().lower())
        search.textChanged.connect(filter_items)
        items.itemActivated.connect(lambda item: entries[items.row(item)][2]())

        def first():
            for i in range(items.count()):
                if not items.item(i).isHidden():
                    entries[i][2]()
                    return
        search.returnPressed.connect(first)
        self.window('launcher', 'Applications', box, (160, 70, 440, 470))
        search.setFocus()

    def closeEvent(self, e):
        layouts = {}
        for key, w in self.windows.items():
            if key in ('files', 'terminal', 'about'):
                r = w.normalGeometry() if w.isMaximized() or w.isMinimized() else w.geometry()
                layouts[key] = [r.x(), r.y(), r.width(), r.height()]
        super().closeEvent(e)
        if e.isAccepted():
            self.settings.setValue('layouts_v3', json.dumps(layouts))
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QSize, QEvent, QUrl
from PySide6.QtGui import QPixmap, QImageReader, QPainter, QDesktopServices
from PySide6.QtWidgets import *
from organizer import Notes, Tasks
from storage import Store
from file_manager import FileManager
from extras import Extras
original_paint = Wallpaper.paintEvent

def paint(self, event):
    original_paint(self, event)
    pix = getattr(self, 'custom_pixmap', None)
    if pix is not None:
        p = QPainter(self.viewport())
        im = pix.scaled(self.viewport().size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        p.drawPixmap((self.width() - im.width()) // 2, (self.height() - im.height()) // 2, im)
Wallpaper.paintEvent = paint

class DesktopFoundation(Extras, ToolDesktop):

    def __init__(self):
        self.store = Store()
        super().__init__()
        self.setWindowTitle('MacaqueSTEP 0.4 — Desktop Preview')
        for key, title, fn, kind in [('notes', 'Notes', self.notes, 'notes'), ('tasks', 'Tasks', self.tasks, 'tasks'), ('media', 'Media Player', self.media, 'media'), ('system', 'System Information', self.system_info, 'system')]:
            self.add_dock(key, title, fn, kind)
        body = self.centralWidget().layout().itemAt(1).layout()
        dock = body.takeAt(1).layout()
        dock.setParent(None)
        widget = QWidget()
        widget.setObjectName('dockPanel')
        widget.setLayout(dock)
        self.dock_scroll = QScrollArea()
        self.dock_scroll.setObjectName('dockScroll')
        self.dock_scroll.setWidgetResizable(True)
        self.dock_scroll.setFrameShape(QFrame.NoFrame)
        self.dock_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dock_scroll.setWidget(widget)
        body.addWidget(self.dock_scroll)
        self.apply_dock_size(int(self.settings.value('dock_size', 48)))
        self.dock_side(self.settings.value('dock_side', 'Right'))
        self.wallpaper(self.settings.value('wallpaper_file', ''))
        self.setMinimumSize(850, 600)
        self.apply_theme(self.theme)

    def apply_theme(self, name):
        super().apply_theme(name)
        bg, panel, fg, line, field = THEMES[self.theme]
        self.setStyleSheet(self.styleSheet() + f'QWidget#dockPanel,QScrollArea#dockScroll {{background:{bg};border:0;}} QHeaderView::section {{background:{panel};color:{fg};border:1px solid {line};padding:5px;}} QCheckBox,QTabWidget {{color:{fg};}}')

    def apply_dock_size(self, size):
        if not hasattr(self, 'dock_scroll'):
            super().apply_dock_size(size)
            return
        size = max(24, min(68, size))
        self.settings.setValue('dock_size', size)
        for b in self.dock_buttons.values():
            b.setFixedSize(size, size)
            b.setIconSize(QSize(size - 18, size - 18))
        self.dock_scroll.setFixedWidth(size + 28)

    def dock_side(self, side):
        self.settings.setValue('dock_side', side)
        if hasattr(self, 'dock_scroll'):
            body = self.centralWidget().layout().itemAt(1).layout()
            body.removeWidget(self.dock_scroll)
            body.insertWidget(0 if side == 'Left' else 1, self.dock_scroll)

    def wallpaper(self, path):
        pix = None
        if path:
            reader = QImageReader(path)
            reader.setAutoTransform(True)
            size = reader.size()
            if size.isValid() and size.width() * size.height() > 60000000:
                return False
            if size.isValid():
                reader.setScaledSize(size.scaled(QSize(3840, 2160), Qt.KeepAspectRatio))
            image = reader.read()
            if image.isNull():
                return False
            pix = QPixmap.fromImage(image)
        self.area.custom_pixmap = pix
        self.settings.setValue('wallpaper_file', path)
        self.area.viewport().update()
        return True

    def reopen(self, key):
        w = self.windows[key]
        w.showNormal()
        w.raise_()
        self.area.setActiveSubWindow(w)
        self.ensure_visible(w)

    def files(self):
        if 'files' in self.windows:
            self.reopen('files')
            return
        self.window('files', 'File Viewer', FileManager(self), (35, 150, 980, 560))

    def open_path(self, p):
        p = Path(p)
        ext = p.suffix.lower()
        if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif'):
            self.images(p)
        elif ext in ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.mp4', '.mkv', '.webm', '.mov'):
            self.media(p)
        elif ext in ('.txt', '.md', '.py', '.sh', '.json', '.conf', '.log', '.csv', '.ini', '.svg', '.xml', '.html', '.css', '.yaml', '.yml', '.desktop'):
            self.editor(p)
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))):
            QMessageBox.warning(self, 'Open', 'No application could open this file.')

    def notes(self):
        if 'notes' in self.windows:
            self.reopen('notes')
            return
        self.window('notes', 'Notes', Notes(self.store), (120, 80, 780, 480))

    def tasks(self):
        if 'tasks' in self.windows:
            self.reopen('tasks')
            return
        self.window('tasks', 'Tasks', Tasks(self.store), (180, 90, 450, 450))

    def window(self, key, title, widget, rect):
        w = super().window(key, title, widget, rect)
        if isinstance(widget, (Notes, FileManager)):
            w.installEventFilter(self)
        return w

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Close and hasattr(obj, 'content'):
            if isinstance(obj.content, Notes) and (not obj.content.flush()):
                event.ignore()
                return True
            if isinstance(obj.content, FileManager) and obj.content.jobs:
                QMessageBox.information(self, 'Copying', 'Wait for the file copy to finish.')
                event.ignore()
                return True
        return super().eventFilter(obj, event)

    def about(self):
        super().about()
        for label in self.windows['about'].content.findChildren(QLabel):
            label.setText(label.text().replace('0.3', '0.4'))

    def launcher(self):
        if 'launcher' in self.windows:
            self.reopen('launcher')
            return
        entries = [('File Viewer', self.files), ('Terminal', self.terminal), ('Text Editor', self.editor), ('Notes', self.notes), ('Tasks', self.tasks), ('Image Viewer', self.images), ('Media Player', self.media), ('Calculator', self.calculator), ('Clock & Timer', self.clock_app), ('System Information', self.system_info), ('Preferences', self.preferences), ('Screenshot', self.screenshot), ('Open Windows', self.window_list), ('About MacaqueSTEP', self.about)]
        box = QWidget()
        v = QVBoxLayout(box)
        search = QLineEdit()
        search.setPlaceholderText('Search 14 desktop tools…')
        items = QListWidget()
        v.addWidget(search)
        v.addWidget(items)
        for name, fn in entries:
            items.addItem(name)

        def filter_items(s):
            for i in range(items.count()):
                items.item(i).setHidden(s.lower() not in items.item(i).text().lower())

        def first():
            for i in range(items.count()):
                if not items.item(i).isHidden():
                    entries[i][1]()
                    return
        search.textChanged.connect(filter_items)
        search.returnPressed.connect(first)
        items.itemActivated.connect(lambda item: entries[items.row(item)][1]())
        self.window('launcher', 'Applications — 14 tools', box, (160, 60, 450, 560))
        search.setFocus()

    def preferences(self):
        if 'preferences' in self.windows:
            self.reopen('preferences')
            return
        super().preferences()
        box = self.windows['preferences'].content
        form = box.layout()
        side = QComboBox()
        side.addItems(['Right', 'Left'])
        side.setCurrentText(self.settings.value('dock_side', 'Right'))
        side.currentTextChanged.connect(self.dock_side)
        form.addRow('Dock position', side)

        def choose():
            p = QFileDialog.getOpenFileName(self, 'Choose wallpaper', str(Path.home()), 'Images (*.png *.jpg *.jpeg *.webp *.bmp)')[0]
            if p and (not self.wallpaper(p)):
                QMessageBox.warning(self, 'Wallpaper', 'Could not load this image. Maximum 60 megapixels.')
        b = QPushButton('Choose wallpaper image…')
        b.clicked.connect(choose)
        form.addRow(b)
        b = QPushButton('Use built-in wallpaper')
        b.clicked.connect(lambda: self.wallpaper(''))
        form.addRow(b)
        self.windows['preferences'].resize(470, 570)
        self.ensure_visible(self.windows['preferences'])

    def closeEvent(self, event):
        for w in list(self.windows.values()):
            if isinstance(w.content, Notes) and (not w.content.flush()):
                event.ignore()
                return
            if isinstance(w.content, FileManager) and w.content.jobs:
                QMessageBox.information(self, 'Copying', 'Wait for the file copy to finish.')
                event.ignore()
                return
        super().closeEvent(event)
