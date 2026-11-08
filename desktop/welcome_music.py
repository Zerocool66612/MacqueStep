"""Original 15-second welcome composition. Synthesized without sampled music."""
import math,struct,wave
from pathlib import Path
DURATION=15
# Warm Cmaj7 / Am7 / Fmaj7 / Gsus / C harmony and a simple original bell line.
CHORDS=[(130.8128,164.8138,195.9977,246.9417),(110.,130.8128,164.8138,195.9977),(87.3071,130.8128,164.8138,220.),(97.9989,146.8324,195.9977,220.),(130.8128,164.8138,195.9977,261.6256)]
MELODY=[(523.2511,.75,0.45),(659.2551,.75,1.2),(783.9909,1.1,2.0),(659.2551,.75,3.5),(523.2511,1.,4.25),(440.,1.,5.1),(523.2511,.8,6.45),(698.4565,.8,7.2),(659.2551,1.,8.),(587.3295,.8,9.5),(783.9909,.9,10.2),(698.4565,.7,11.),(659.2551,.8,12.15),(523.2511,2.1,12.9)]
def samples(rate=22050):
    score=[(freq,3.35,i*3,.18) for i,chord in enumerate(CHORDS) for freq in chord]+[(f,d,t,.28) for f,d,t in MELODY]
    out=[]
    for i in range(int(DURATION*rate)):
        t=i/rate;value=0.
        for freq,dur,onset,gain in score:
            phase=t-onset
            if 0<=phase<dur:
                envelope=min(1,phase/.06)*min(1,(dur-phase)/.42)*math.exp(-phase*.9/dur)
                value+=gain*envelope*(math.sin(math.tau*freq*phase)+.10*math.sin(math.tau*freq*phase*2))
        value*=min(1,t/.3)*min(1,(DURATION-t)/1.2)
        out.append(value)
    peak=max(abs(v) for v in out) or 1
    return [round(v/peak*14000) for v in out]
def write(path):
    data=samples()
    with wave.open(str(path),'wb') as w:w.setparams((1,2,22050,0,'NONE','not compressed'));w.writeframes(struct.pack('<'+'h'*len(data),*data))
if __name__=='__main__':write(Path(__file__).parent/'assets/sounds/welcome.wav')
