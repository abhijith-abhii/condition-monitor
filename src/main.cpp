#include "monitor.hpp"
#include <Arduino.h>
#include <Preferences.h>
#include <SPI.h>
#include <atomic>
#include <esp_system.h>
#include <esp_task_wdt.h>
constexpr int CS = 26, IRQ = 27;
struct SpiBus {
    bool read(uint8_t reg, uint8_t *data, size_t n) {
        SPI.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE3));
        digitalWrite(CS, LOW);
        SPI.transfer(reg | 0x80 | (n > 1 ? 0x40 : 0));
        for (size_t i = 0; i < n; ++i)
            data[i] = SPI.transfer(0);
        digitalWrite(CS, HIGH);
        SPI.endTransaction();
        return true; // SPI has no ACK; identity/status checks detect absence.
    }
    bool write(uint8_t reg, uint8_t value) {
        SPI.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE3));
        digitalWrite(CS, LOW);
        SPI.transfer(reg);
        SPI.transfer(value);
        digitalWrite(CS, HIGH);
        SPI.endTransaction();
        return true;
    }
};
struct Report {
    uint32_t ms, seq, gaps, compute_us;
    float rms, crest;
    uint8_t state;
};
QueueHandle_t samples, reports;
TaskHandle_t sampler;
std::atomic<uint32_t> sample_drops{0}, report_drops{0}, overruns{0};
void IRAM_ATTR watermark() {
    BaseType_t wake = pdFALSE;
    if (sampler)
        vTaskNotifyGiveFromISR(sampler, &wake);
    if (wake)
        portYIELD_FROM_ISR();
}
void acquire(void *) {
    esp_task_wdt_add(nullptr);
#ifndef SIMULATED_SENSORS
    SpiBus bus;
    monitor::Adxl345<SpiBus> sensor{bus};
    uint32_t last = millis();
    bool ready = false;
#endif
    uint32_t seq = 0;
    bool pending_gap = false;
    for (;;) {
        esp_task_wdt_reset();
#ifdef SIMULATED_SENSORS
        ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(20));
        for (int i = 0; i < 16; ++i) {
            float amp = (seq / 800 % 20 >= 10) ? 0.45f : 0.05f;
            monitor::Sample s{seq,
                              int16_t((0.3f + amp * sinf(2 * PI * 50 * seq / 800.0f)) / 0.0039f),
                              uint16_t(pending_gap)};
            ++seq;
            if (xQueueSend(samples, &s, 0) != pdTRUE) {
                ++sample_drops;
                pending_gap = true;
            } else
                pending_gap = false;
        }
#else
        if (!ready) {
            ready = sensor.begin();
            if (!ready) {
                monitor::Sample fault{seq++, 0, 1};
                xQueueSend(samples, &fault, 0);
                vTaskDelay(pdMS_TO_TICKS(1000));
                continue;
            }
            last = millis();
            pending_gap = true;
        }
        ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(10));
        uint8_t n = 0;
        bool overrun = false;
        if (!sensor.status(n, overrun)) {
            ready = false;
            continue;
        }
        if (overrun) {
            ++overruns;
            pending_gap = true;
        }
        if (n)
            last = millis();
        for (unsigned i = 0; i < n; ++i) {
            int16_t x;
            if (!sensor.sample(x)) {
                ready = false;
                break;
            }
            monitor::Sample s{seq++, x, uint16_t(pending_gap)};
            if (xQueueSend(samples, &s, 0) != pdTRUE) {
                ++sample_drops;
                pending_gap = true;
            } else
                pending_gap = false;
            delayMicroseconds(5); // ADXL FIFO pop needs at least 5 us between reads.
        }
        if (core::elapsed(millis(), last) >= 100) {
            monitor::Sample fault{seq++, 0, 1};
            xQueueSend(samples, &fault, 0);
            ready = false;
        }
#endif
    }
}
void analyze(void *) {
    esp_task_wdt_add(nullptr);
    monitor::Processor processor;
    monitor::Sample s;
    monitor::Features f;
    for (;;) {
        esp_task_wdt_reset();
        if (xQueueReceive(samples, &s, pdMS_TO_TICKS(100)) != pdTRUE) {
            processor.used = 0;
            processor.detector.fault();
            Report r{millis(), 0, processor.gaps, 0, 0, 0, uint8_t(monitor::State::SENSOR_FAULT)};
            if (xQueueSend(reports, &r, 0) != pdTRUE)
                ++report_drops;
            continue;
        }
        uint32_t t = micros();
        bool complete = processor.accept(s, f);
        uint32_t us = micros() - t;
        if (complete || s.flags) {
            Report r{millis(),
                     s.sequence,
                     processor.gaps,
                     us,
                     complete ? f.rms : 0,
                     complete ? f.crest : 0,
                     uint8_t(processor.detector.state)};
            if (xQueueSend(reports, &r, 0) != pdTRUE)
                ++report_drops;
        }
    }
}
void setup() {
    Serial.begin(115200);
    pinMode(CS, OUTPUT);
    digitalWrite(CS, HIGH);
    SPI.begin(18, 19, 23, CS);
    pinMode(IRQ, INPUT);
    Serial.printf("# reset=%d simulated=%d\n", int(esp_reset_reason()),
#ifdef SIMULATED_SENSORS
                  1
#else
                  0
#endif
    );
    esp_task_wdt_init(5, true);
    samples = xQueueCreate(128, sizeof(monitor::Sample));
    reports = xQueueCreate(8, sizeof(Report));
    if (!samples || !reports) {
        Serial.println("# fatal queue allocation");
        delay(1000);
        ESP.restart();
    }
    if (xTaskCreatePinnedToCore(acquire, "sample", 4096, nullptr, 3, &sampler, 1) != pdPASS ||
        xTaskCreatePinnedToCore(analyze, "analyze", 4096, nullptr, 2, nullptr, 1) != pdPASS) {
        Serial.println("# fatal task allocation");
        delay(1000);
        ESP.restart();
    }
    attachInterrupt(digitalPinToInterrupt(IRQ), watermark, RISING);
    esp_task_wdt_add(nullptr);
    Serial.println("ms,sequence,rms_g,crest,state,gaps,sample_drops,report_drops,overruns,compute_"
                   "us,free_heap,stack_free");
}
void loop() {
    static Preferences prefs;
    static bool opened = prefs.begin("monitor", false);
    static int state = -1;
    static uint32_t last_save = 0;
    static bool dirty = false;
    static bool announced = false;
    Report r;
    if (!announced) {
        Serial.printf("# persisted_state=%u NVS=%d\n",
                      opened ? prefs.getUChar("last_state", 255) : 255, opened);
        announced = true;
    }
    esp_task_wdt_reset();
    if (xQueueReceive(reports, &r, pdMS_TO_TICKS(100)) == pdTRUE) {
        Serial.printf("%u,%u,%.5f,%.3f,%u,%u,%u,%u,%u,%u,%u,%u\n", r.ms, r.seq, r.rms, r.crest,
                      r.state, r.gaps, sample_drops.load(), report_drops.load(), overruns.load(),
                      r.compute_us, ESP.getFreeHeap(),
                      unsigned(uxTaskGetStackHighWaterMark(nullptr)));
        if (state != r.state) {
            state = r.state;
            dirty = true;
        }
    }
    if (dirty && opened && core::elapsed(millis(), last_save) >= 60000) {
        if (prefs.putUChar("last_state", uint8_t(state)) == 1) {
            dirty = false;
            last_save = millis();
        } else {
            Serial.println("# NVS write failed");
            last_save = millis();
        }
    }
}
