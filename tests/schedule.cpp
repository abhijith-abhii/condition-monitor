#include "monitor.hpp"
#include <cassert>
#include <iostream>
// Discrete-event FIFO/queue model, not FreeRTOS or ESP32 cycle emulation.
int main() {
    core::Ring<int16_t, 32> fifo;
    core::Ring<monitor::Sample, 128> queue;
    monitor::Processor processor;
    monitor::Features features;
    uint32_t sequence = 0, overruns = 0, windows = 0;
    bool hardware_gap = false, software_gap = false;
    for (unsigned tick = 0; tick < 4000; ++tick) { // 5 s at 800 Hz
        if (fifo.count == 32) {
            fifo.pop(); // stream FIFO overwrites oldest
            ++overruns;
            hardware_gap = true;
        }
        assert(fifo.push(int16_t(tick % 40)));
        // 10 ms fallback poll, interrupted by a 50 ms sampling blackout.
        if (tick % 8 == 0 && !(tick >= 400 && tick < 440)) {
            while (fifo.front()) {
                monitor::Sample sample{sequence++, *fifo.front(),
                    uint16_t(hardware_gap || software_gap)};
                fifo.pop();
                hardware_gap = false;
                if (!queue.push(sample)) software_gap = true;
                else software_gap = false;
            }
        }
        // Analysis blackout for 300 ms exercises bounded software capacity.
        if (!(tick >= 1600 && tick < 1840)) {
            while (queue.front()) {
                if (processor.accept(*queue.front(), features)) ++windows;
                queue.pop();
            }
        }
        assert(fifo.count <= 32 && queue.count <= 128);
    }
    assert(overruns > 0 && queue.drops > 0 && processor.gaps > 0);
    assert(windows > 0 && windows < 4000 / monitor::WINDOW);
    assert(queue.count == 0);
    std::cout << "PASS discrete-event fault model: hardware_overruns=" << overruns
              << " queue_drops=" << queue.drops << " invalidated_windows=" << processor.gaps
              << " completed_windows=" << windows << "; simulated_duration_s=5\n";
}
