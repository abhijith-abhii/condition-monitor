# Understanding machine condition monitor

The sensor collects acceleration on its own clock. A sampling task drains its FIFO, an analysis task groups samples into windows, and a low-priority task prints the results. A window is 256 samples or 320 ms at the configured 800 Hz rate. Subtracting the mean removes static gravity and mounting offset. RMS describes vibration strength; crest factor describes peakiness. Three high windows enter alarm and five low windows clear it.

## Code walkthrough

### include/monitor.hpp: features

Walk through mean, centered energy, square root, peak and crest. The baseline passes remove_dc=false.

### include/monitor.hpp: Detector

Draw NORMAL, ALARM and SENSOR_FAULT. Explain consecutive high/low counts and the neutral band.

### include/monitor.hpp: Processor

Trace 255 samples, a missing sequence, and 256 fresh samples. A discontinuity must not masquerade as a clean window.

### include/monitor.hpp: Adxl345

Explain identity register 0x00, format 0x31, rate 0x2c, FIFO 0x38 and 6-byte sample reads.

### src/main.cpp: acquire / analyze / loop

Follow ownership and priorities. Explain how notifications wake acquisition and queues isolate slow serial output.

### tools/simulate.cpp

Show the same feature and detector code receiving deterministic synthetic signals. This is a host simulation, not MCU emulation.

## Ten interview questions

### 1. Why subtract the mean?

Static gravity or a mounting offset raises raw RMS even when dynamic vibration stays small. Centering estimates the AC component within each window.

### 2. Why use a FIFO?

The sensor clock determines sample spacing. The CPU can drain small batches, reducing interrupt frequency and tolerating brief scheduling delays. Capacity still limits delay tolerance.

### 3. What happens when the queue fills?

The new sample is dropped and counted. A sequence discontinuity or explicit gap flag resets the partial window, so detection never silently treats discontinuous data as continuous.

### 4. Why is the ISR short?

SPI and printing can block. The ISR only notifies a task; bounded work reduces interrupt latency and leaves scheduling available.

### 5. How fast can an alarm appear?

For the aligned simulated step, three 320 ms windows require 960 ms. An arbitrary onset and mixed first window can add delay; physical latency remains unmeasured.

### 6. What does crest factor add?

Peak divided by RMS distinguishes peaky from smooth signals. It is logged for explanation and future work; the current alarm rule uses RMS only.

### 7. Why is no DMA used?

Each sensor sample is a small separate SPI transaction with FIFO-pop timing. DMA complexity has no demonstrated benefit here.

### 8. Is a fault the same as an alarm?

No. ALARM means qualified elevated vibration. SENSOR_FAULT means insufficient trustworthy samples. Reporting them separately avoids presenting missing data as a healthy machine.

### 9. What is thread-safe here?

Queue copies transfer samples and reports; one task owns each peripheral; atomic integers hold diagnostic counters. Volatile alone would not provide cross-core synchronization.

### 10. What would make it industrial?

Calibrated mounting, full-axis acquisition, spectral validation, labeled operating data, electrical protection, field fault tests and measured timing. None can be inferred from synthetic accuracy.

## Five minute demonstration

1. Run sh tools/test.sh and identify the gap/overflow assertions.
2. Run sh tools/simulate.sh and open evidence/benchmark.png.
3. Explain the offset region, five isolated spikes and sustained step. Show the delayed alarm as a tradeoff.
4. Open src/main.cpp and trace one interrupt through the queues. End by stating that target timing is pending hardware.

## Independent exercises

- Add y/z axes and compare vector RMS with separate-axis RMS. Extend analytic tests first.
- Make thresholds configurable with versioned storage and reject NaN or inverted thresholds.
- Add a Goertzel feature for a known rotation frequency and validate with two synthetic tones.

## Resume wording and contribution

These describe the implemented artifact and recorded tests. The code was generated with AI assistance in this session; do not present it as independently authored or physically validated. Use these bullets only after you can reproduce and explain the implementation, and retain the AI-assisted description where it accurately reflects your contribution.

- Developed an AI-assisted C++ vibration-monitoring prototype with an ADXL345 adapter, FreeRTOS queues, gap detection and persistent diagnostics; cross-compiled for ESP32.
- Validated mean-removed RMS and alarm hysteresis with analytic inputs, mocked SPI faults and repeated host execution.
- Reduced isolated-spike alarms from 5 to 0 on a deterministic synthetic trace, with sustained-alarm delay increasing from 0.32 s to 0.96 s.

For a later hardware achievement, first execute the numbered experiments in hardware.md, retain raw captures and revise the bullet with the actual sample count and measured result. No physical percentage, battery lifetime, throughput or accuracy is supplied as a placeholder.
