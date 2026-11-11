# Portfolio requirements established before implementation

Status: provisional hardware; no board or instruments confirmed. Date: 2026-11-11.
Target: classic dual-core ESP32-WROOM-32 DevKitC, 4 MB flash, USB serial.
Toolchain: PlatformIO Core 6.1.18, espressif32 6.9.0, Arduino ESP32 2.0.17,
Xtensa GCC 8.4.0. C++ portable application cores and ESP32 adapters.
All results must say host, simulated, cross-compiled, analytical, or physical.

## Flagship condition monitor
User: small workshop technician checking a fan or motor for a sustained change.
Environment: dry indoor bench, rigid sensor mount, low-voltage equipment only.
F1: ADXL345 SPI identity check, full-resolution +/-16g, 800 Hz hardware sampling,
32-entry FIFO; interrupt watermark 16; bounded polling fallback at 10 ms.
F2: 256-sample x-axis windows; remove DC; calculate RMS and crest factor;
three consecutive RMS windows above 0.20g enter alarm; five below 0.14g clear.
These are demonstration thresholds, not a trained bearing-fault diagnosis.
F3: FIFO overrun and queue drops invalidate partial windows and are counted;
missing data for 100 ms reports sensor fault; retry sensor initialization in 1 s.
F4: producer priority 3, analysis priority 2, output priority 1; bounded queues;
no SPI, allocation, printing, or processing in ISR. Task watchdog 5 s.
F5: publish window records at 115200 baud and save alarm transitions in NVS;
flash persistence limited to one write per 60 s (pending last transition retained).
Targets: zero unreported loss; process window <10 ms on target; recovery <2 s;
static application queues <8 KiB; firmware fits default 1.25 MiB app partition.
Baseline: raw RMS without DC removal and single-window threshold. Improved:
DC removal and persistence/hysteresis. Compare identical synthetic waveforms.
Hardware budget estimate USD: board 10-18, ADXL345 module 5-12, wire/mount 5-10.
Acceptance: host analytic signal tests, injected data gaps, queue full, alarm
transitions, driver transactions; target build. Sampling timing and watchdog
reset require board, logic analyzer, and serial capture.

## Environment logger
User: hobby greenhouse operator retaining readings during gateway outages.
E1: SHT31 at I2C 0x44, 3.3 V, 100 kHz; single-shot high repeatability; validate
both CRC bytes; reject partial frames and invalid readings. Bus timeout 50 ms.
E2: sample once per wake then sleep 60 s; ring holds 32 records in NVS with
version and CRC; allocate monotonically increasing 32-bit sequence identifiers.
E3: UART gateway sends ACK for exact oldest sequence; bounded frame parser;
up to three attempts per record, 250 ms per attempt, at most four records/wake.
Gateway uses SQLite durable insert/dedup before ACK. Cold reset reloads queue.
E4: overflow drops newest sample, increments persistent loss counter; invalid
sensor reading creates no record; failed persistence prohibits transmission.
Targets: exact retained-record delivery in deterministic outage simulation;
CRC rejects every tested single-bit corruption; active wake <5 s (target test);
record store <1 KiB. No measured power target until board is selected.
Baseline: fire-and-forget loses outage samples. Improved: bounded persistent
queue, exact ACK, retransmission and duplicate suppression; same outage trace.
Budget estimate USD: board 10-18, SHT31 module 8-18, wires 3-5; battery power
hardware excluded pending user choice. DevKit regulator/USB LED limits sleep.
Acceptance: CRC vectors, truncation, wrap, queue full, ACK errors, corruption,
restart simulation, real local gateway integration, target build. Physical power,
I2C recovery, NVS interruption and deep-sleep retention remain board tests.

## Pulse recorder
User: lab operator measuring a low-voltage fan/test rig's speed and run time.
P1: GPIO27 rising edges, <=1 kHz, reject edges <500 us apart; ISR only counts
and timestamps under a short critical section; 100 ms reporting task snapshots.
P2: rollover-safe elapsed time, configurable 1-32 pulses/revolution; speed from
count difference and actual elapsed time; 2 s without accepted edge => STALLED.
P3: GPIO25 LED indicator via 1 kohm resistor; UART PPR n command with bounded
parser; validated version/CRC persistent configuration; restart loads config.
P4: runtime counts intervals with recent pulses; sample ADC1 GPIO34 for a
0-3.3 V test potentiometer as raw counts (not calibrated voltage); serial CSV.
Targets: no lost accepted pulses <=1 kHz (board test); exact host counter wrap;
report jitter p99 <5 ms (board); stall indicator <=2.1 s after final pulse;
malformed input never changes configuration. Watchdog 5 s.
Baseline: fixed 100 ms denominator; improved: actual elapsed time. Compare
same deterministic schedule jitter trace. Budget USD: board 10-18, pot/LED/
resistors/wires 5-10; use second board/function generator for bench pulses.
Acceptance: rollover, debounce model, idle/stall, parser boundaries, config CRC,
jitter simulation, target build. No machine shutdown or safety function.

## Portfolio measurement plan
Ten metrics: F1 DC-offset RMS error; F2 isolated-spike false alarms; F3 sustained
alarm delay; E1 delivery fraction; E2 duplicate transmissions; P1 speed error
under jitter; P2 simulated stall delay; all-project firmware flash; all-project
static RAM; host core soak throughput and duration. Record baseline/final,
method, environment, workload, sample count and limitations for each. Physical
latency, jitter, CPU, stack, power and battery life remain explicit experiments.
