# Scope and engineering decisions

- User confirmed no sensors and requested simulation; intermediate C and comfortable C++.
- Physical designs are retained. All execution evidence is host/simulated or cross-compilation.
- Use one affordable ESP32-WROOM DevKitC sequentially for all three projects if bought later.
- Benchmarks exercise the same portable headers compiled into ESP32 firmware. They do not emulate FreeRTOS, an ESP32 CPU, flash timing, electrical faults, or real sensor noise.
- UART telemetry is deliberately local and offline. No cloud credentials, wireless availability, or paid simulation service is necessary.
- Project-specific code: sensor transaction logic, signal features, state machines, bounded queues/parsers, reliability protocol, gateway, simulations, tests, and reports.
- Framework: Arduino ESP32 supplies peripheral HAL, startup and serial; ESP-IDF supplies FreeRTOS, watchdog, sleep and NVS; SQLite supplies transactional gateway storage.
- No DMA added: ADXL345 FIFO samples require separate 6-byte reads and a pop interval. DMA setup is not justified by this workload; measure before changing it.
- Target dependency versions are pinned for reproducibility, not claimed to be the newest release.
- Initial generic ADXL345 budget is superseded by the documented Adafruit 1231 option at USD 17.50, observed 2026-11-11. SHT31 option is Adafruit 2857 at USD 13.95. Board/accessory budgets remain estimates, excluding tax/shipping.
- An initial persistent-store size assertion was corrected from 288 to 284 bytes; a long-idle microsecond rollover defect was fixed and regression-tested. Original failure logs are retained.
- Default thresholds demonstrate sustained vibration change, not industrial fault classification. Calibration, mounting and labeled machine data are future work.
- Work was generated, implemented and tested with AI assistance. The user has not claimed to assemble, flash, measure, or independently author it. Resume templates must preserve that distinction.
