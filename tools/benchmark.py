#!/usr/bin/env python3
"""Reproduce host traces and metrics. Never treats host timings as MCU timings."""
import argparse,csv,json,os,pathlib,platform,statistics,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
NAME=json.loads((ROOT/'docs/report-content.json').read_text())['id']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rerun',action='store_true',help='Compile and regenerate trace plus repeated host runs')
    ap.add_argument('--seconds',type=float,default=5.0)
    ap.add_argument('--extended-seconds',type=float,default=60.0)
    args=ap.parse_args()
    if args.rerun:
        with (ROOT/'evidence/trace.csv').open('w') as f:subprocess.run(['sh','tools/simulate.sh'],cwd=ROOT,stdout=f,check=True)
        repeats=[]
        for i in range(3):
            d=json.loads(subprocess.check_output([str(ROOT/'.build/simulate'),'--soak',str(args.seconds)]))
            d.update(repeat=i+1,environment=platform.platform(),kind='host benchmark',unit='256-sample windows' if NAME=='condition-monitor' else 'state updates')
            repeats.append(d)
        (ROOT/'evidence/soak.json').write_text(json.dumps(repeats,indent=2)+'\n')
        d=json.loads(subprocess.check_output([str(ROOT/'.build/simulate'),'--soak',str(args.extended_seconds)]))
        d.update(environment=platform.platform(),kind='host extended loop; not hardware endurance',duration_target_seconds=args.extended_seconds)
        (ROOT/'evidence/extended-soak.json').write_text(json.dumps(d,indent=2)+'\n')
    rows=list(csv.DictReader((ROOT/'evidence/trace.csv').open()))
    env=platform.platform()+'; C++17 -O2; portable application core'
    metrics=[]
    def metric(id,name,definition,method,workload,n,baseline,final,units,limits,kind='deterministic simulation'):
        metrics.append(dict(id=id,metric=name,definition=definition,measurement_method=method,environment=('ESP32-WROOM; Xtensa GCC 8.4.0; Arduino 2.0.17; PlatformIO 6.9.0' if kind=='cross-compilation' else env),workload=workload,sample_count_or_duration=n,baseline=baseline,final_result=final,units=units,limitations=limits,kind=kind))
    if NAME=='condition-monitor':
        subset=[r for r in rows if r['scenario']=='dc_offset']
        errors=lambda key:statistics.mean(abs(float(r[key])-float(r['true_rms'])) for r in subset)
        metric('M01','DC offset RMS error','Mean absolute error against amplitude/sqrt(2)','Same analytic sine through features(remove_dc=false/true)','50 Hz sine, 0.05 g peak, +0.3 g DC; 800 Hz sampling','50 windows x 256 samples',errors('baseline_rms'),errors('final_rms'),'g','Ideal float input; no sensor calibration, quantization or noise')
        subset=[r for r in rows if r['scenario']=='isolated_spike']
        metric('M02','Isolated spike alarm count','Alarm-positive windows on isolated one-window bursts','Count flags in identical trace','Five 0.45 g one-window sines separated by quiet windows','5 injected bursts',sum(int(r['baseline_alarm']) for r in subset),sum(int(r['final_alarm']) for r in subset),'alarms','Synthetic event test only; not field false-alarm rate')
        subset=[r for r in rows if r['scenario']=='sustained']
        start=float(subset[0]['seconds'])-.32
        delay=lambda key:float(next(r for r in subset if r[key]=='1')['seconds'])-start
        metric('M03','Sustained alarm delay','First alarm window end minus aligned signal onset','Find first positive flag after sustained-step onset','0.45 g sine starting at a window boundary','30 sustained windows',delay('baseline_alarm'),delay('final_alarm'),'s','Simulation time; arbitrary onset can delay more; no scheduling or UART latency')
    elif NAME=='environment-logger':
        end=rows[-1]
        metric('M04','Delivery fraction','Unique delivered sequence IDs / generated readings','Run fire-and-forget and persistent queue on identical online trace','120 wakes; offline wakes 20..39; first ACK lost for sequences divisible by 7','120 generated readings',100*int(end['baseline_delivered'])/120,100*int(end['final_delivered'])/120,'percent','Outage shorter than capacity; no real UART or NVS timing')
        metric('M05','Duplicate transmissions','Data frames received after their ID was already received','Set insertion failure counter in model','Same outage and ACK-loss workload as M04','120 readings; '+end['attempts']+' final attempts',0,int(end['duplicate_transmissions']),'frames','Reliability costs extra transmissions; SQLite dedup checked separately')
    else:
        subset=[r for r in rows if int(r['step'])<150]
        err=lambda k:statistics.mean(abs(float(r[k])-float(r['true_rpm'])) for r in subset)
        metric('M06','Speed normalization error','Mean absolute RPM error','Fixed 100 ms vs measured elapsed interval on same counts','3000 RPM; 2 PPR; repeated 80/100/120/90/110 ms schedule','150 running intervals',err('baseline_rpm'),err('final_rpm'),'RPM','Ideal phase-aligned integer pulse counts; real quantization remains')
        last=int(subset[-1]['time_us']);stall=next(int(r['time_us']) for r in rows if int(r['step'])>=150 and r['stalled']=='1')
        metric('M07','Stall delay','First stalled report minus final pulse timestamp','Read timestamp difference from stopped trace','Pulse train ends after step 149','50 stopped intervals',None,(stall-last)/1e6,'s','No baseline stall algorithm; simulation time only; target <=2.1 s')
    buildfile=ROOT/'evidence/build-esp32dev.json'
    if buildfile.exists():
        build=json.loads(buildfile.read_text())
        for id,key,label in [('M08','flash','Firmware flash footprint'),('M09','ram','Firmware static RAM')]:
            metric(id,label,'PlatformIO linked image usage','Parse target linker size report','Physical-input ESP32 firmware','1 target build',None,build[key]['used_bytes'],'bytes','No baseline firmware image; static RAM excludes runtime heap, queues and task stacks','cross-compilation')
    soak=json.loads((ROOT/'evidence/soak.json').read_text());rates=[d['iterations']/d['duration_seconds'] for d in soak]
    metric('M10','Host core throughput','Completed workload units per measured wall second','steady_clock around compiled C++ core; observable checksum','256-sample processing windows' if NAME=='condition-monitor' else ('enqueue, seal, validate, ACK' if NAME=='environment-logger' else 'elapsed-time recorder updates'),str(len(soak))+' repetitions, durations '+','.join("%.6fs" % d["duration_seconds"] for d in soak),None,statistics.median(rates),'units/s','Desktop benchmark only; no baseline speedup claim; min='+str(min(rates))+' max='+str(max(rates)),'host benchmark')
    (ROOT/'evidence/metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    with (ROOT/'evidence/metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=metrics[0].keys());writer.writeheader();writer.writerows(metrics)
    print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
