from __future__ import annotations
from dataclasses import dataclass,field
import time

@dataclass
class RecordedEvent:
    at:float
    kind:str
    value:str

@dataclass
class MacroRecording:
    name:str='Recording'
    events:list[RecordedEvent]=field(default_factory=list)
    started:float=0.0
    active:bool=False
    def start(self): self.events.clear(); self.started=time.monotonic(); self.active=True
    def add(self,kind,value):
        if self.active:self.events.append(RecordedEvent(time.monotonic()-self.started,kind,str(value)))
    def stop(self): self.active=False; return list(self.events)
    def as_steps(self):
        steps=[]; last=0.0
        for e in self.events:
            delay=max(0,e.at-last)
            if delay:steps.append({'type':'wait','seconds':round(delay,3)})
            if e.kind=='tap':steps.append({'type':'tap','key':e.value})
            elif e.kind=='click':steps.append({'type':'click','button':e.value})
            last=e.at
        return steps

TEMPLATES={
 'Stationary Use':[{'type':'click','button':'right'},{'type':'wait','seconds':1}],
 'Walk and Use':[{'type':'hold','key':'w','seconds':1},{'type':'click','button':'right'}],
 'Slot Use Return':[{'type':'slot','slot':2},{'type':'click','button':'right'},{'type':'slot','slot':1}],
}
