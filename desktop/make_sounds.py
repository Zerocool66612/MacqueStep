#!/usr/bin/env python3
"""Synthesize original, freely reusable retro workstation sound effects."""
import math,random,wave,struct
from pathlib import Path
RATE=22050
EVENTS={
 'startup':(.92,[(0,261.63,.62),(.12,329.63,.64),(.25,392,.62),(.43,523.25,.48)]),
 'open':(.16,[(0,523.25,.10),(.06,783.99,.10)]),
 'close':(.15,[(0,659.25,.09),(.06,392,.09)]),
 'minimize':(.18,[(0,587.33,.10),(.06,440,.10),(.11,293.66,.07)]),
 'restore':(.18,[(0,293.66,.10),(.06,440,.10),(.11,587.33,.07)]),
 'menu':(.055,[(0,1046.5,.045)]),
 'click':(.045,[(0,740,.03)]),
 'workspace':(.13,[(0,392,.10),(.035,523.25,.09)]),
 'alert':(.42,[(0,440,.15),(.20,440,.16)]),
 'error':(.32,[(0,196,.19),(.13,185,.16)]),
 'trash':(.27,[(0,140,.11),(.07,220,.08),(.15,100,.11)]),
 'complete':(.36,[(0,523.25,.13),(.10,659.25,.14),(.20,783.99,.15)])}
def synthesize(name,duration,notes):
 random_source=random.Random(91+sum(map(ord,name)));output=[];noise=0
 for index in range(int(duration*RATE)):
  t=index/RATE;sample=0
  for onset,freq,length in notes:
   dt=t-onset
   if 0<=dt<length:
    envelope=min(1,dt/.008)*math.exp(-4*dt/length)*min(1,(length-dt)/.018)
    phase=2*math.pi*freq*dt
    tone=math.sin(phase+.8*math.sin(phase*2)*math.exp(-12*dt))+.17*math.sin(phase*3)
    sample+=tone*envelope*.27
  if name in ('click','trash','menu'):
   noise=.65*noise+.35*random_source.uniform(-1,1);sample+=noise*.12*math.exp(-t/(.012 if name!='trash' else .09))
  sample=max(-.9,min(.9,sample));output.append(int(sample*32767))
 return output
if __name__=='__main__':
 root=Path(__file__).with_name('assets')/'sounds';root.mkdir(parents=True,exist_ok=True)
 for name,(duration,notes) in EVENTS.items():
  samples=synthesize(name,duration,notes)
  with wave.open(str(root/(name+'.wav')),'wb') as file:file.setnchannels(1);file.setsampwidth(2);file.setframerate(RATE);file.writeframes(struct.pack('<'+'h'*len(samples),*samples))
 print('Generated',len(EVENTS),'original sound effects')
