# Engineering review and release gates

This is a simulation-validated prototype with target-compilation evidence. It is
not evidence of senior job tenure, hardware bring-up, certification, or field
reliability. The interview value is the reasoning and reproducible evidence.

## Timing and resource budget

| Resource | Budget / derivation | Evidence boundary |
|---|---|---|
| ADXL345 FIFO | 32 / 800 = 40 ms total depth; 16-sample watermark = 20 ms | Analytical capacity, not measured latency |
| Sampling fallback | 10 ms poll; nominally <=8 new samples per poll | RTOS/flash stalls can exceed this; detect overruns |
| Sample queue | 128 x 8 = 1024 payload bytes, plus RTOS control overhead | Allocated at startup; no unbounded growth |
| Analysis window | 256 x 4 = 1024 bytes | Processor owns the array |
| Worker stacks | 4096 bytes for each of two flagship tasks | Allocated heap; not included in static RAM linker count |
| Report queue | 8 copied records; drop count on full | Output can lose rows, never silently claim completeness |
| Telemetry store | 284-byte versioned blob, 32 x 8-byte records | Compile-time layout guard; ABI-specific format |
| Telemetry wait | 4 records x 3 attempts x 250 ms <=3 s ACK waiting | Plus sensor, serial, flash and scheduler time; measure <5 s target |
| Pulse snapshots | 100 ms; modular elapsed valid below 2^32 us | Long idle age saturates; task watchdog bounds severe hangs |
| ISR pulse input | <=1 kHz, 500 us debounce | Requires measured ISR time and count fidelity |

SPI at 2 MHz needs 28 us for a 1-byte command plus 6-byte sample, plus the
5 us FIFO interval and software overhead. Sixteen samples therefore have a
528 us wire-plus-gap lower bound. This is **not WCET**: locking, interrupts,
flash stalls and HAL costs remain unmeasured. No hard real-time guarantee is made.

## Failure mode and recovery analysis

| Failure | Detection | Response | Remaining exposure / release gate |
|---|---|---|---|
| Missing accelerometer | Identity, invalid FIFO count, 100 ms silence | Fault state; 1 s reinitialization retry | Valid-looking corrupt SPI words cannot be CRC-checked |
| FIFO or sample queue overflow | Sensor flag, drop counter, sequence gap | Discard partial window; require new data | Dropped data is unrecoverable; field load test needed |
| Slow serial reader | Report queue full | Drop and count report | Complete event history is not guaranteed |
| Stuck task | Registered 5 s watchdog | SDK panic/restart behavior | Actual reset injection not yet run on a board |
| Sensor CRC or truncated frame | Both CRC-8 words and length | Skip invalid environmental sample | Hard-stuck bus needs physical recovery experiment |
| Gateway outage | Exact ACK timeout | Retain oldest; bounded retries; later wake | At most 32 unacknowledged samples retained |
| Lost ACK | Replay same device/sequence | Gateway durable deduplication | More transmissions and energy |
| Reset before local dequeue save | Old record remains in NVS | Safe replay after restart | Flash atomicity and wear need real power-cut tests |
| Corrupt queue blob | Magic, version, shape, CRC-32 | No transmission; explicit repair | Cannot salvage corrupted data automatically |
| Sequence exhaustion | Allocator reaches reserved zero | Reject new samples | Requires explicit new provisioning epoch |
| Input chatter | Minimum 500 us accepted-edge separation | Reject count increments | Too-fast legitimate pulses are also rejected |
| Long-idle timer wrap | Saturating idle age | Stay stalled until fresh count | Snapshot must still run before one timer wrap |
| Bad configuration command | Bounded parser and range checks | No live/NVS update | Trusted local UART; no authentication |

## Version comparison contract

B0 denotes the deliberately simple reference algorithms executed in simulate.cpp:
raw RMS / one-window alarm, fire-and-forget telemetry, and fixed 100 ms speed
normalization. R1 denotes the final shared-core behavior and compiled adapters.
These are algorithm variants tested on identical inputs, **not two historical
field deployments**. The first failed tests are retained independently.

Each metric records definition, method, environment, workload, count/duration,
baseline, result and limitations in metrics.csv. Null baseline means no baseline
measurement exists; it never means zero. Improvement claims are limited to the
specific trace, and regressions or costs remain visible.

## Release gates beyond the current prototype

1. Demonstrate sensor identity and actual wiring on a physical board.
2. Measure sampling cadence, service latency and deadline misses under serial and
   flash stress. Retain raw traces, instrument setup and firmware checksum.
3. Perform sensor disconnection, bus lock, watchdog and power-cut experiments.
4. Measure sleep energy and flash write behavior before battery/endurance claims.
5. Validate real machine signals and mounting before selecting alarm thresholds.
6. Explain every ownership boundary and reproduce each result without relying on
   a memorized claim. Implement at least one independent extension and add tests.

## Change discipline

Keep current and baseline workloads together. Record a failing test before a
fix when a defect is found. Rerun affected tests and target builds; compare raw
outputs and document what improved, regressed, or remained unmeasured. Use
failures.md for the dated defect ledger. Avoid retroactively presenting new
results as historical measurements.
