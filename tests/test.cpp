#include <chrono>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <set>
#include <vector>
static unsigned checks = 0;
#define CHECK(x)                                                                                   \
    do {                                                                                           \
        ++checks;                                                                                  \
        if (!(x)) {                                                                                \
            std::cerr << "FAIL line " << __LINE__ << ": " << #x << "\n";                           \
            std::exit(1);                                                                          \
        }                                                                                          \
    } while (0)

#include "monitor.hpp"
struct Mock {
    uint8_t regs[64]{};
    bool fail = false;
    std::vector<std::pair<int, int>> writes;
    bool read(uint8_t r, uint8_t *p, size_t n) {
        if (fail)
            return false;
        std::memcpy(p, regs + r, n);
        return true;
    }
    bool write(uint8_t r, uint8_t v) {
        if (fail)
            return false;
        regs[r] = v;
        writes.push_back({r, v});
        return true;
    }
};
int main() {
    float wave[256];
    for (int i = 0; i < 256; ++i)
        wave[i] = 0.7f + 0.1f * std::sin(2 * 3.141592653589793 * 16 * i / 256);
    auto f = monitor::features(wave, 256);
    CHECK(std::abs(f.rms - 0.1 / std::sqrt(2)) < 1e-6);
    CHECK(std::abs(f.crest - std::sqrt(2)) < 1e-5);
    CHECK(monitor::features(wave, 0).rms == 0);
    for (auto &v : wave)
        v = 4;
    CHECK(monitor::features(wave, 256).rms == 0);
    monitor::Detector d;
    CHECK(d.update(.3f) == monitor::State::NORMAL);
    CHECK(d.update(.3f) == monitor::State::NORMAL);
    CHECK(d.update(.3f) == monitor::State::ALARM);
    for (int i = 0; i < 4; ++i)
        CHECK(d.update(.1f) == monitor::State::ALARM);
    CHECK(d.update(.1f) == monitor::State::NORMAL);
    CHECK(d.update(std::numeric_limits<float>::quiet_NaN()) == monitor::State::SENSOR_FAULT);
    CHECK(d.update(.1) == monitor::State::NORMAL);
    d.update(.3);
    d.update(.17);
    d.update(.3);
    CHECK(d.high == 1);
    d.fault();
    CHECK(d.high == 0);
    monitor::Processor p;
    for (unsigned i = 0; i < 255; ++i)
        CHECK(!p.accept({i, 10, 0}, f));
    CHECK(p.accept({255, 10, 0}, f));
    CHECK(!p.accept({300, 10, 0}, f));
    CHECK(p.gaps == 1 && p.used == 1 && p.detector.state == monitor::State::SENSOR_FAULT);
    CHECK(!p.accept({301, 10, 1}, f));
    CHECK(p.used == 0 && p.gaps == 2);
    p = monitor::Processor{};
    p.accept({UINT32_MAX, 1, 0}, f);
    p.accept({0, 1, 0}, f);
    CHECK(p.gaps == 0);
    core::Ring<int, 2> q;
    CHECK(q.push(1) && q.push(2));
    CHECK(!q.push(3) && q.drops == 1);
    CHECK(*q.front() == 1);
    q.pop();
    q.push(4);
    CHECK(*q.front() == 2);
    q.pop();
    CHECK(*q.front() == 4);
    q.pop();
    CHECK(!q.pop());
    Mock bus;
    monitor::Adxl345<Mock> drv{bus};
    CHECK(!drv.begin());
    bus.regs[0] = 0xe5;
    CHECK(drv.begin());
    CHECK(bus.regs[0x31] == 0x0b && bus.regs[0x2c] == 0x0d && bus.regs[0x38] == 0x90 &&
          bus.regs[0x2e] == 3);
    bus.regs[0x39] = 32;
    bus.regs[0x30] = 1;
    uint8_t n;
    bool over;
    CHECK(drv.status(n, over) && n == 32 && over);
    bus.regs[0x39] = 63;
    CHECK(!drv.status(n, over));
    bus.regs[0x32] = 0x00;
    bus.regs[0x33] = 0x80;
    int16_t x;
    CHECK(drv.sample(x) && x == -32768);
    bus.fail = true;
    CHECK(!drv.begin() && !drv.sample(x));
    std::cout << "PASS " << checks
              << " assertions: features, hysteresis, gaps, ring, mocked SPI driver\n";
}
