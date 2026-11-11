#include <chrono>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <set>
using Clock = std::chrono::steady_clock;

#include "monitor.hpp"
int main(int argc, char **argv) {
    if (argc > 1 && std::string(argv[1]) == "--soak") {
        double duration = argc > 2 ? std::atof(argv[2]) : 10;
        auto start = Clock::now();
        uint64_t iterations = 0;
        monitor::Processor p;
        monitor::Features f;
        uint32_t seq = 0;
        volatile double sum = 0;
        do {
            for (int j = 0; j < 256; ++j) {
                if (p.accept({seq++, int16_t(int(seq % 100) - 50), 0}, f))
                    sum += f.rms;
            }
            ++iterations;
        } while (std::chrono::duration<double>(Clock::now() - start).count() < duration);
        std::cout << std::setprecision(12) << "{\"duration_seconds\":"
                  << std::chrono::duration<double>(Clock::now() - start).count()
                  << ",\"iterations\":" << iterations << ",\"checksum\":" << sum << "}\n";
        return 0;
    }
    std::cout
        << "window,seconds,scenario,true_rms,baseline_rms,final_rms,baseline_alarm,final_alarm\n";
    monitor::Detector detector;
    float x[256];
    for (int w = 0; w < 200; ++w) {
        double amplitude = 0.05, offset = 0;
        const char *scenario = "quiet";
        if (w < 50) {
            offset = .3;
            scenario = "dc_offset";
        } else if (w < 100 && w % 10 == 0) {
            amplitude = .45;
            scenario = "isolated_spike";
        } else if (w >= 100 && w < 130) {
            amplitude = .45;
            scenario = "sustained";
        }
        for (int i = 0; i < 256; ++i)
            x[i] = float(offset + amplitude * std::sin(2 * 3.141592653589793 * 16 * i / 256));
        auto baseline = monitor::features(x, 256, false), final = monitor::features(x, 256, true);
        auto state = detector.update(final.rms);
        std::cout << std::setprecision(9) << w << ',' << (w + 1) * .32 << ',' << scenario << ','
                  << amplitude / std::sqrt(2) << ',' << baseline.rms << ',' << final.rms << ','
                  << (baseline.rms > .2) << ',' << (state == monitor::State::ALARM) << '\n';
    }
}
