#pragma once
#include "common.hpp"
#include <cmath>
namespace monitor {
constexpr size_t WINDOW = 256;
struct Features {
    float rms = 0, crest = 0;
};
// Two passes avoid catastrophic cancellation in E[x*x]-E[x]^2.
inline Features features(const float *x, size_t n, bool remove_dc = true) {
    if (!n)
        return {};
    double mean = 0, sum = 0, peak = 0;
    if (remove_dc) {
        for (size_t i = 0; i < n; ++i)
            mean += x[i];
        mean /= n;
    }
    for (size_t i = 0; i < n; ++i) {
        double v = x[i] - mean;
        sum += v * v;
        if (std::abs(v) > peak)
            peak = std::abs(v);
    }
    double rms = std::sqrt(sum / n);
    return {float(rms), float(rms > 1e-9 ? peak / rms : 0)};
}
enum class State : uint8_t { NORMAL, ALARM, SENSOR_FAULT };
struct Detector {
    State state = State::NORMAL;
    uint8_t high = 0, low = 0;
    void fault() {
        state = State::SENSOR_FAULT;
        high = low = 0;
    }
    State update(float rms) {
        if (!std::isfinite(rms) || rms < 0) {
            fault();
            return state;
        }
        // A complete valid window recovers sensing; alarm qualification starts anew.
        if (state == State::SENSOR_FAULT)
            state = State::NORMAL;
        if (rms > 0.20f) {
            low = 0;
            if (high < 3)
                ++high;
            if (high >= 3)
                state = State::ALARM;
        } else if (rms < 0.14f) {
            high = 0;
            if (low < 5)
                ++low;
            if (low >= 5)
                state = State::NORMAL;
        } else {
            high = low = 0;
        }
        return state;
    }
};
struct Sample {
    uint32_t sequence;
    int16_t x;
    uint16_t flags;
};
struct Processor {
    float window[WINDOW]{};
    size_t used = 0;
    uint32_t expected = 0, gaps = 0;
    bool started = false;
    Detector detector;
    bool accept(const Sample &s, Features &f) {
        if ((started && s.sequence != expected) || s.flags) {
            ++gaps;
            used = 0;
            detector.fault();
        }
        started = true;
        expected = s.sequence + 1;
        if (s.flags)
            return false;
        window[used++] = float(s.x) * 0.0039f;
        if (used != WINDOW)
            return false;
        f = features(window, WINDOW);
        used = 0;
        detector.update(f.rms);
        return true;
    }
};
// Bus contract: read/write return false on transport error; adapter owns SPI.
template <class Bus> struct Adxl345 {
    Bus &bus;
    bool begin() {
        uint8_t id = 0;
        if (!bus.read(0x00, &id, 1) || id != 0xe5)
            return false;
        return bus.write(0x2d, 0) && bus.write(0x31, 0x0b) && bus.write(0x2c, 0x0d) &&
               bus.write(0x38, 0) && bus.write(0x38, 0x90) && bus.write(0x2f, 0) &&
               bus.write(0x2e, 0x03) && bus.write(0x2d, 0x08);
    }
    bool status(uint8_t &entries, bool &overrun) {
        uint8_t src = 0, n = 0;
        if (!bus.read(0x30, &src, 1) || !bus.read(0x39, &n, 1))
            return false;
        entries = n & 0x3f;
        overrun = (src & 1) != 0;
        return entries <= 32;
    }
    bool sample(int16_t &x) {
        uint8_t b[6];
        if (!bus.read(0x32, b, 6))
            return false;
        x = int16_t(uint16_t(b[0]) | (uint16_t(b[1]) << 8));
        return true;
    }
};
} // namespace monitor
