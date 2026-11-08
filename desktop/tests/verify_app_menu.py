"""Exercise the global menus against real documents, files and clipboard state."""
import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sandbox=tempfile.TemporaryDirectory(prefix='step-menus-');root=Path(sandbox.name)
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
from PySide6.QtPrintSupport import QPrinter
from backup_app import create_backup,schedule_restore,apply_pending_restore
app=QApplication([]);d=Desktop();d.resize(1450,950);d.show();QTest.qWait(300);bar=d.app_menu

def action(menu,name):
 bar.populate(menu);return next(a for a in bar.menus[menu].actions() if a.objectName()==name)
def activate(w,target=None):
 d.activate_running(w.property('running_key'),False)
 if target:target.setFocus()
 QTest.qWait(20)
try:
 assert d.bar_style()=='classic' and d.menu_stack.currentWidget() is bar and d.menu_stack.height()==30
 assert list(bar.menus)==['MacaqueSTEP','File','Edit','View','Go','Window','Help']
 # Editor menu adapters retain existing Save/Open safeguards and atomically save actual content.
 w=d.editor();activate(w,w.content.editor);edit=w.content.editor;edit.setPlainText('alpha beta');edit.document().setModified(True);path=root/'document.txt'
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'Text')):action('File','file.save').trigger()
 assert path.read_text()=='alpha beta' and not edit.document().isModified()
 other=root/'opened.txt';other.write_text('opened by File menu')
 with patch.object(QFileDialog,'getOpenFileName',return_value=(str(other),'')):action('File','file.open').trigger()
 assert edit.toPlainText()=='opened by File menu'
 # Editing routes to the last focused control, with real selection and undo/redo state.
 edit.selectAll();assert action('Edit','edit.copy').isEnabled();action('Edit','edit.copy').trigger();assert QApplication.clipboard().text()=='opened by File menu'
 action('Edit','edit.cut').trigger();assert edit.toPlainText()=='';assert action('Edit','edit.undo').isEnabled();action('Edit','edit.undo').trigger();assert edit.toPlainText()=='opened by File menu';assert action('Edit','edit.redo').isEnabled()
 QApplication.clipboard().setText('replacement');edit.selectAll();action('Edit','edit.paste').trigger();assert edit.toPlainText()=='replacement'
 edit.selectAll();action('Edit','edit.delete').trigger();assert edit.toPlainText()=='';edit.document().setModified(False)
 # Notes search/title fields use text editing, while notes File commands call organizer operations.
 d.notes();notes=d.windows['notes'];activate(notes,notes.content.title);notes.content.title.setText('Note title');notes.content.title.selectAll();action('Edit','edit.copy').trigger();assert QApplication.clipboard().text()=='Note title'
 notes.content.body.setPlainText('Saved from menu');notes.content.dirty=True;action('File','file.save').trigger();assert any(row[1]=='Note title' and row[2]=='Saved from menu' for row in d.store.notes())
 # File Viewer uses file URLs in its main view and normal text selection in its location field.
 d.files();files=d.windows['files'];fm=files.content;fm.navigate(root);QTest.qWait(120);fm.view.setCurrentIndex(fm.model.index(str(path)));activate(files,fm.view);action('Edit','edit.copy').trigger();assert QApplication.clipboard().mimeData().hasUrls()
 captured=[]
 with patch.object(fm,'start_transfer',side_effect=lambda *args:captured.append(args)):action('Edit','edit.paste').trigger()
 assert captured and str(path) in captured[0][0]
 fm.path.selectAll();fm.path.setFocus();QTest.qWait(10);action('Edit','edit.copy').trigger();assert QApplication.clipboard().text()==str(root)
 # Read-only terminal supports copying and explicit PTY paste, with destructive text edits disabled.
 d.terminal();terminal=d.windows['terminal'];activate(terminal,terminal.content.view);QApplication.clipboard().setText('echo test');sent=[]
 with patch.object(terminal.content,'write',side_effect=sent.append):action('Edit','edit.paste').trigger()
 assert sent==[b'echo test'];assert not action('Edit','edit.cut').isEnabled();assert not action('Edit','edit.delete').isEnabled()
 # Paint exposes real undo and PNG saving, and disables text paste.
 d.paint_app();paint=d.windows['paint'];activate(paint);paint.content.canvas.snapshot();paint.content.canvas.image.fill(Qt.red);paint.content.canvas.dirty=True;assert action('Edit','edit.undo').isEnabled();action('Edit','edit.undo').trigger();assert not action('Edit','edit.paste').isEnabled()
 image=root/'drawing.png'
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(image),'PNG')):action('File','file.save').trigger()
 assert image.exists() and not paint.content.canvas.dirty
 # PDF rendering exercises the print path without sending anything to a real printer.
 activate(w,edit);edit.setPlainText('MacaqueSTEP menu print test');edit.document().setModified(False);printer=QPrinter();printer.setOutputFormat(QPrinter.PdfFormat);pdf=root/'printed.pdf';printer.setOutputFileName(str(pdf));assert action('File','file.print').isEnabled();bar.render_print(w,printer);assert pdf.read_bytes().startswith(b'%PDF') and pdf.stat().st_size>500
 painter_printer=QPrinter();painter_printer.setOutputFormat(QPrinter.PdfFormat);paint_pdf=root/'paint.pdf';painter_printer.setOutputFileName(str(paint_pdf));bar.render_print(paint,painter_printer);assert paint_pdf.read_bytes().startswith(b'%PDF')
 w.content.findChild(QLineEdit).setFocus();QTest.qWait(10);assert action('File','file.print').isEnabled()
 # A canceled close keeps the editor; stale actions cannot act on a replacement window.
 edit.insertPlainText('unsaved')
 with patch.object(QMessageBox,'question',return_value=QMessageBox.No):action('File','file.close').trigger()
 assert w.property('running_key') in d.windows;edit.document().setModified(False)
 stale=action('File','file.save');w.close();QTest.qWait(30);stale.trigger()
 # All menus can populate with no selected window; unsupported actions stay disabled.
 d.area.setActiveSubWindow(None)
 for name in bar.menus:bar.populate(name)
 assert not action('File','file.close').isEnabled() and not action('File','file.save').isEnabled()
 # Three styles use the same central layout structure; hidden/restore remembers the chosen bar.
 d.set_bar_style('toolbar');assert d.menu_stack.currentWidget() is d.desktop_toolbar;d.set_top_bar_visible(False);assert d.menu_stack.isHidden();d.toggle_top_bar();assert d.bar_style()=='toolbar';d.set_bar_style('classic');assert d.centralWidget().layout().count()==2
 d.preferences();combo=d.findChild(QComboBox,'desktopBarStyle');assert combo.currentData()=='classic';combo.setCurrentIndex(combo.findData('none'));assert d.menu_stack.isHidden();d.toggle_top_bar();assert combo.currentData()=='classic'
 backup=root/'backup.zip';create_backup(d.store,d.settings,backup);schedule_restore(backup);restored=QSettings(str(root/'restored.ini'),QSettings.IniFormat);assert apply_pending_restore(restored);assert restored.value('desktop_bar_style')=='classic'
 d.close();QTest.qWait(50);d2=Desktop();d2.show();QTest.qWait(300);assert d2.bar_style()=='classic' and d2.menu_stack.currentWidget() is d2.app_menu;d2.close();QTest.qWait(50)
 print('PASS classic menu layout, real editor save/open/edit/undo, focused-field routing, Notes and file clipboard commands, Terminal paste, Paint save/undo, PDF printing, close cancellation/stale actions, disabled states, style selection, backups and restart')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:
   for window in widget.windows.values():
    if hasattr(window.content,'editor'):window.content.editor.document().setModified(False)
    if isinstance(window.content,Paint):window.content.canvas.dirty=False
   widget.close()
 app.processEvents()
