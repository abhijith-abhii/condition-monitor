# Official references and GitHub design study

Reviewed 2026-11-11. These are design references, not vendored source copies.

1. [Analog Devices ADXL345 Rev G datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/adxl345.pdf): registers, full-resolution scale, FIFO, SPI mode, and FIFO-pop timing.
2. [Sensirion SHT3x DIS version 7 datasheet](https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf): single-shot transaction, conversion equations, CRC polynomial and reference vector.
3. [Espressif DevKitC hardware guide](https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32/hw-reference/esp32/get-started-devkitc.html): board pin functions and flash-reserved pins.
4. [Espressif task watchdog documentation](https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32/api-reference/system/wdts.html): task registration, reset and timeouts.
5. [PlatformIO Espressif platform 6.9.0](https://github.com/platformio/platform-espressif32/blob/v6.9.0/platform.json): framework and compiler versions.
6. [Espressif timer wake example at Arduino 2.0.17](https://github.com/espressif/arduino-esp32/blob/2.0.17/libraries/ESP32/examples/DeepSleep/TimerWakeUp/TimerWakeUp.ino): reviewed wake-source configuration and serial flush before sleep. This portfolio adds a persistent queue and durable gateway protocol.
7. [Sensirion SHT3x driver at commit 4026a907](https://github.com/Sensirion/embedded-i2c-sht3x/blob/4026a907aa9045ffc2a2813302e8ee5e69c96846/sht3x_i2c.c): reviewed separation of transport, measurement and conversion; this portfolio implements its own minimal transaction driver with exact rounded integer conversions and mocks.
8. [Analog Devices no-OS ADXL345 driver](https://github.com/analogdevicesinc/no-OS/blob/main/drivers/accel/adxl345/adxl345.c): reviewed identity probing and register transport separation. Retrieved file blob SHA f1b1464fd0dba8dc2f11f27c97b284f63f20ce41; main may change. Portfolio adapter owns SPI in one task and adds bounded processing queues.
9. [Adafruit 1231 ADXL345](https://www.adafruit.com/product/1231) and [pinout guide](https://learn.adafruit.com/adxl345-digital-accelerometer/pinouts): documented breakout, USD 17.50 observed; 3.3 V VIN keeps interface logic at 3.3 V.
10. [Adafruit 2857 SHT31](https://www.adafruit.com/product/2857): documented 0x44/0x45 breakout, USD 13.95 observed; pull-ups are already present.

Dependency licensing remains with the original projects. No third-party driver code was copied into the custom application headers. Tool-downloaded framework binaries contain their own licensed components.
