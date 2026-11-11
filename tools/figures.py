#!/usr/bin/env python3
import csv,json,pathlib,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.build/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
BLUE='#155e75';ORANGE='#bd5b2d';INK='#152838'
rows=list(csv.DictReader((ROOT/'evidence/trace.csv').open()))
meta=json.loads((ROOT/'docs/report-content.json').read_text())
name=meta['id']
fig,axes=plt.subplots(2,1,figsize=(9,5.5),layout='constrained')
if name=='condition-monitor':
 x=[float(r['seconds']) for r in rows]
 for key,label,color in [('baseline_rms','Baseline raw RMS',ORANGE),('final_rms','Improved centered RMS',BLUE)]:axes[0].plot(x,[float(r[key]) for r in rows],label=label,color=color,lw=1.8)
 axes[0].axhline(.2,color='gray',ls='--',lw=.8,label='Alarm threshold')
 axes[0].set_ylabel('Acceleration RMS (g)')
 axes[1].step(x,[int(r['baseline_alarm'])+.04 for r in rows],label='Single-window rule',color=ORANGE,where='post')
 axes[1].step(x,[int(r['final_alarm']) for r in rows],label='Persistence + hysteresis',color=BLUE,where='post')
 axes[1].set_yticks([0,1],['Normal','Alarm']);axes[1].set_xlabel('Simulated time (s)')
elif name=='environment-logger':
 x=[int(r['wake']) for r in rows]
 for key,label,color in [('baseline_delivered','Fire-and-forget',ORANGE),('final_delivered','Persistent + ACK',BLUE)]:axes[0].plot(x,[int(r[key]) for r in rows],label=label,color=color,lw=2)
 axes[0].set_ylabel('Unique delivered records')
 axes[1].plot(x,[int(r['queued']) for r in rows],color=BLUE,label='Queued records')
 axes[1].plot(x,[int(r['duplicate_transmissions']) for r in rows],color=ORANGE,label='Cumulative retransmissions')
 axes[1].set_ylabel('Records / frames');axes[1].set_xlabel('Simulated wake cycle')
 for ax in axes:ax.axvspan(20,39,color='#e2e8f0',label='Gateway offline')
else:
 subset=rows[:30];x=[int(r['step']) for r in subset]
 axes[0].plot(x,[float(r['baseline_rpm']) for r in subset],color=ORANGE,label='Fixed 100 ms denominator',marker='.',lw=1)
 axes[0].plot(x,[float(r['final_rpm']) for r in subset],color=BLUE,label='Actual elapsed time',lw=2)
 axes[0].set_ylabel('Calculated RPM');axes[0].set_xlabel('Running report index')
 subset=rows[140:];x=[int(r['time_us'])/1e6 for r in subset]
 axes[1].step(x,[int(r['stalled']) for r in subset],where='post',color=BLUE,label='Stall state')
 axes[1].axvline(15,color=ORANGE,ls='--',label='Final pulse')
 axes[1].set_yticks([0,1],['Running','Stalled']);axes[1].set_xlabel('Simulated time (s)')
for ax in axes:ax.grid(axis='y',alpha=.2);ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),fontsize=8,ncol=3,frameon=False)
fig.suptitle(meta['title']+' | deterministic simulation',fontsize=14,fontweight='bold',color=INK)
fig.savefig(ROOT/'evidence/benchmark.png',dpi=180);plt.close(fig)
# Functional block diagram; not a PCB layout.
fig,ax=plt.subplots(figsize=(9,2.5),layout='constrained');ax.set_xlim(0,9);ax.set_ylim(0,2.6);ax.axis('off')
for i,label in enumerate(meta['arch']):
 row=i//3;col=i%3 if row==0 else 2-i%3;x=.15+col*3;y=1.5-row*1.3
 ax.add_patch(FancyBboxPatch((x,y),2.6,.7,boxstyle='round,pad=0.06',facecolor='#edf5f7',edgecolor=BLUE))
 words=label.split();cut=max(1,len(words)//2);label=' '.join(words[:cut])+'\n'+' '.join(words[cut:])
 ax.text(x+1.3,y+.35,label,ha='center',va='center',fontsize=10,color=INK)
 if row==0 and col<2:ax.annotate('',xy=(x+2.88,y+.35),xytext=(x+2.65,y+.35),arrowprops={'arrowstyle':'->','color':BLUE})
 if row==1 and col>0:ax.annotate('',xy=(x-.32,y+.35),xytext=(x-.08,y+.35),arrowprops={'arrowstyle':'->','color':BLUE})
ax.annotate('',xy=(7.45,.98),xytext=(7.45,1.44),arrowprops={'arrowstyle':'->','color':BLUE})
fig.savefig(ROOT/'docs/architecture.png',dpi=180);plt.close(fig)
# Explicit one-wire-per-row connection diagram, with named endpoints.
n=len(meta['wiring']);fig,ax=plt.subplots(figsize=(9,1+n*.54),layout='constrained');ax.axis('off');ax.set_xlim(0,10);ax.set_ylim(-.5,n+.8)
ax.text(.2,n+.2,'ESP32 / source',fontsize=12,fontweight='bold',color=INK)
ax.text(6,n+.2,'Destination',fontsize=12,fontweight='bold',color=INK)
for i,(left,right,note) in enumerate(meta['wiring']):
 y=n-1-i
 ax.text(.2,y,left,va='center',fontsize=10)
 ax.text(6,y,right,va='center',fontsize=10)
 ax.annotate('',xy=(5.8,y),xytext=(3.3,y),arrowprops={'arrowstyle':'-','color':BLUE,'lw':1.6})
fig.savefig(ROOT/'docs/wiring.png',dpi=180);plt.close(fig)
print('Saved benchmark, architecture and wiring figures for',name)
