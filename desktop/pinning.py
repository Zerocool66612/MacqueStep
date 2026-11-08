"""Persistent app pins, independent of running-window lifetime."""
import hashlib,json,uuid
from PySide6.QtWidgets import QMessageBox
from dock_workspace import valid_entry,entries_json,ACTION
from drawers import INTERNAL
from running_dock import app_kind
def identity(entry):
 entry=valid_entry(entry)
 if entry is None:return None
 return ('action',entry['action']) if 'action' in entry else ('command',entry['command'])
def pin_group(entry):return 'pinned:'+hashlib.sha256(json.dumps(identity(entry)).encode()).hexdigest()
class Pinning:
 def bottom_pins(self):
  rows=entries_json(self.settings,'running_pins_v14',[]);seen=set();result=[]
  for entry in rows:
   key=identity(entry)
   if key not in seen:result.append(entry);seen.add(key)
  return result
 def is_pinned(self,entry,destination):
  entries=self.bottom_pins() if destination=='running' else getattr(self,'side_launchers',[])
  return any(identity(row)==identity(entry) for row in entries)
 def set_pin(self,entry,destination,pinned=True):
  entry=valid_entry(entry)
  if entry is None or destination not in ('side','running'):return False
  entries=self.bottom_pins() if destination=='running' else list(self.side_launchers);key=identity(entry)
  if pinned:
   if any(identity(row)==key for row in entries):return True
   if len(entries)>=100:QMessageBox.information(self,'Dock full','This dock supports up to 100 pinned launchers.');return False
   entry['id']=uuid.uuid4().hex;entries.append(entry)
  else:entries=[row for row in entries if identity(row)!=key]
  if destination=='running':self.settings.setValue('running_pins_v14',json.dumps(entries))
  else:self.write_location({'type':'side'},entries)
  if hasattr(self,'clip'):self.refresh_docks()
  if hasattr(self,'running_dock'):self.running_dock.signature=None;self.queue_running_refresh()
  return True
 def pin_menu(self,menu,entry):
  if valid_entry(entry) is None:return
  menu.addSeparator()
  for title,destination in [('side dock','side'),('running-app dock','running')]:
   pinned=self.is_pinned(entry,destination);label=('Unpin from ' if pinned else 'Pin to ')+title
   menu.addAction(label,lambda checked=False,e=dict(entry),where=destination,value=not pinned:self.set_pin(e,where,value))
 def entry_for_window(self,key):
  action=ACTION.get(app_kind(key))
  return {'name':INTERNAL[action],'action':action} if action in INTERNAL else None
 def entry_for_callback(self,callback):
  action={'paint_app':'paint','search_files':'search','clock_app':'clock'}.get(getattr(callback,'__name__',''),getattr(callback,'__name__',''))
  return {'name':INTERNAL[action],'action':action} if action in INTERNAL else None
