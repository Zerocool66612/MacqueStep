"""User data and conservative filesystem operations."""
import os,sqlite3,shutil
from pathlib import Path

def data_root():
 p=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'MacaqueSTEP'/'preview';p.mkdir(parents=True,exist_ok=True);return p

class Store:
 def __init__(self,path=None):
  self.db=sqlite3.connect(str(path or data_root()/'organizer.sqlite3'))
  self.db.execute('CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY,title TEXT NOT NULL,body TEXT NOT NULL DEFAULT "")')
  self.db.execute('CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0)');self.db.commit()
 def notes(self):return self.db.execute('SELECT id,title,body FROM notes ORDER BY id DESC').fetchall()
 def add_note(self,title='Untitled note'):
  with self.db:return self.db.execute('INSERT INTO notes(title,body) VALUES (?,?)',(title,'')).lastrowid
 def save_note(self,n,title,body):
  with self.db:self.db.execute('UPDATE notes SET title=?,body=? WHERE id=?',(title,body,n))
 def delete_note(self,n):
  with self.db:self.db.execute('DELETE FROM notes WHERE id=?',(n,))
 def tasks(self):return self.db.execute('SELECT id,title,done FROM tasks ORDER BY done,id DESC').fetchall()
 def add_task(self,title):
  with self.db:return self.db.execute('INSERT INTO tasks(title) VALUES (?)',(title,)).lastrowid
 def set_task(self,n,done):
  with self.db:self.db.execute('UPDATE tasks SET done=? WHERE id=?',(int(done),n))
 def clear_done(self):
  with self.db:self.db.execute('DELETE FROM tasks WHERE done=1')

def duplicate_file(source,destination):
 """Copy one regular file without overwriting another path, even on a collision."""
 src=Path(source);dst=Path(destination)
 if src.is_symlink() or not src.is_file():raise ValueError('Copy supports regular files. Choose a file, not a folder or symbolic link.')
 try:
  with src.open('rb') as reader, dst.open('xb') as writer:
   try:shutil.copyfileobj(reader,writer,1024*1024)
   except BaseException:
    writer.close();dst.unlink(missing_ok=True);raise
 except FileExistsError:raise FileExistsError('An item with that name already exists. Rename it or choose another folder.')
 return str(dst)
