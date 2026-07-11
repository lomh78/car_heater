<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/dark_logo.png" width="250">
  <img alt="Car Heater Logo" src="docs/images/logo.png" width="250">
</picture>

# 🚗 Car Heater

A Home Assistant integration for controlling engine heaters (block heaters) with intelligent pre-heating based on outdoor temperature and departure time.

The integration automatically calculates the optimal heating time and provides sensors and controls that can be used in dashboards, automations and the included Car Heater Card.

---

## Features

- 🚗 Automatic runtime calculation
- 📈 Configurable heating curve
- ✏️ Manual runtime configuration
- 🕒 Manual, Workday and One-Time departure
- 📅 Workday support
- 📊 Runtime history
- 🌡 Temperature history
- ⚡ Power history
- 🔥 Heating Curve sensor
- 🎯 Timeline support
- 🌍 English and Swedish translations
- 🧩 Fully configurable through the Home Assistant UI
- ❤️ HACS compatible

---

## Installation

### HACS

Search for **Car Heater** in HACS and install the integration.

Restart Home Assistant after installation.

---

## Configuration

After installation, add the integration from:

Settings → Devices & Services → Add Integration

Select:

- Temperature sensor
- Heater switch
- Optional power sensor

Configure:

- Temperature limit
- Longest runtime
- Automatic or manual runtime calculation
- Departure times
- Workday options

---

## Sensors

The integration creates several entities including:

- Status
- Runtime
- Start time
- Stop time
- Heating Curve
- Timeline

---

## Companion Card

For the best user experience install the companion **Car Heater Card**.

It provides:

- Timeline
- Runtime history
- Temperature graph
- Power graph
- Heating Curve
- One-Time Departure slider

---

## Screenshots

(Add screenshots here)

---

## Requirements

- Home Assistant 2025.6 or newer
- HACS (recommended)

---

## License

MIT License
