"""Explicit lifecycle journal/proof IO adapter; original journal/guards unchanged."""
from pathlib import Path
import os,sys
from .cleanup import cleanup
from .foundation.journal_base import FileIO
class BudgetFileIO(FileIO):
 def __init__(self,budget,owner='lifecycle',hook=None):super().__init__(hook);self.budget=budget;self.owner=owner;self.paths={};self.closing=False
 def open_exclusive(self,path):
  path=self.budget._path(path,self.owner,self.closing);self.budget.ensure(self.owner,4096,closing=self.closing)
  self.hook('open',str(path),0);fd=self.budget.secure_open(self.owner,path,closing=self.closing);self.paths[fd]=path;return fd
 def write(self,fd,data):
  if fd not in self.paths:raise ValueError('BUDGET_FILEIO_UNOWNED_FD')
  return self.budget.write_fd(self.owner,self.paths[fd],fd,data,lambda:super(BudgetFileIO,self).write(fd,data),closing=self.closing)
 def fsync(self,fd):
  try:return super().fsync(fd)
  except BaseException as e:
   self.budget.poison(e);raise
 def close(self,fd):
  primary=sys.exc_info()[1];notes=len(getattr(primary,'__notes__',()));closed=[]
  def operation():super(BudgetFileIO,self).close(fd);closed.append(True)
  result=cleanup(primary,[('lifecycle-file-close',operation)])
  if closed:self.paths.pop(fd,None)
  if result is not primary or len(getattr(result,'__notes__',()))>notes:
   try:self.budget.poison(result)
   except BaseException as storage:result.add_note('LIFECYCLE_CLOSE_POISON_SECONDARY:'+type(storage).__name__+':'+str(storage)[:256])
  if primary is None and result is not None:raise result
