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

## 💻 Image
<h2 id="gallery">📷 Project Gallery</h2>

<p align="center">
  <img src="https://github.com/user-attachments/assets/f0da540e-523d-4061-b861-4703ece624d0" width="31%" alt="Image 1 - صورة القطعة النهائية" />
  <img src="https://github.com/user-attachments/assets/3d52a34b-3a0d-4a42-8030-b8112bbd0aee" width="31%" alt="Image 2 - CAD model" />
  <img src="https://github.com/user-attachments/assets/ebb7d5c1-7f82-49fa-a5bb-53cc249d7943" width="31%" alt="Image 3 - CAD model" />
</p>

---

## 🚀 Future Enhancements (V2)
- **Miniaturization:** Transitioning from the current breadboard/off-the-shelf component phase to a **Custom PCB design**.
- **Ergonomics:** Shrinking the enclosure size for a more wearable and comfortable commercial design.
