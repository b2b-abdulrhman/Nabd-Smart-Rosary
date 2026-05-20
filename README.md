# Nabd (نبض) - Smart Rosary Prototype 📿💡

An integrated embedded system prototype designed to merge daily spiritual traditions with modern technology. "Nabd" features a digital Qibla compass and a synchronized prayer times display, all optimized to run efficiently on a microcontroller.

---

## ⚙️ Features
- **Precise Qibla Direction:** Integrated digital compass to locate the Qibla dynamically.
- **Prayer Times Display:** Real-time synchronized display for daily prayer times.
- **Power Management:** Deep Sleep Mode integration to optimize and extend battery life during inactivity.
- **Memory Optimization:** Custom-tailored display library to minimize RAM and storage consumption.

---

## 🛠️ Hardware Components (V1)
- **Microcontroller:** Raspberry Pi Pico
- **Display:** TFT st7789
- **Sensor:** HMC5883L
- **Power:** Lithium with a custom voltage reading circuit (ADC).
- **Enclosure:** Custom 3D-printed structure designed via CAD.

---

## 💻 Software & Firmware
- **Language:** MicroPython
- **Key Techniques:** Battery level monitoring via ADC, display library refactoring, and deep sleep scheduling.

---

## 🚀 Future Enhancements (V2)
- **Miniaturization:** Transitioning from the current breadboard/off-the-shelf component phase to a **Custom PCB design**.
- **Ergonomics:** Shrinking the enclosure size for a more wearable and comfortable commercial design.
