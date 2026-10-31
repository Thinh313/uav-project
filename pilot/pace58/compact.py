"""Bounded contiguous observers; no change to durable WAL record/write/barrier."""
from array import array
from wal_journal import Wal
class Rows:
 def __init__(self,capacity,width):self.capacity,self.width,self.count=capacity,width,0;self.data=array('Q',[0])*(capacity*width)
 def append(self,row):
  if self.count>=self.capacity:raise RuntimeError('TRACE_CAPACITY_NO_DROP')
  if len(row)!=self.width:raise ValueError('TRACE_WIDTH')
  values=array('Q',row);start=self.count*self.width;self.data[start:start+self.width]=values;self.count+=1
 def __len__(self):return self.count
 def __iter__(self):
  for i in range(self.count):yield list(self.data[i*self.width:(i+1)*self.width])
class CompactWal(Wal):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.append_cost=array('Q',self.append_cost);self.flush_cost=array('Q',self.flush_cost)
