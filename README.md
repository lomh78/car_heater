<p align="center">
  <img src="docs/images/logo.png" width="180" alt="Car Heater logo">
</p>

# Car Heater

A Home Assistant custom integration for engine block heaters / car heaters.

## Features

- Temperature-based runtime calculation
- Multiple temperature sensor fallback
- Optional workday schedule
- Manual departure time
- Start now and stop buttons
- Optional power sensor
- Custom Lovelace card
- Swedish and English translations
- Prepared for HACS/GitHub releases

## Installation: integration

Copy this folder to Home Assistant:

```text
custom_components/car_heater
```

Restart Home Assistant and add **Car Heater** from **Settings → Devices & services**.

## Installation: custom card

Copy this folder to Home Assistant:

```text
www/community/car-heater-card
```

Add this Lovelace resource:

```yaml
url: /local/community/car-heater-card/car-heater-card.js
 type: module
```

## Example card

```yaml
type: custom:car-heater-card
# Add the entity IDs created by the integration here
```

## Project layout

```text
custom_components/car_heater/       Home Assistant integration
custom_card/car-heater-card/        Lovelace custom card
docs/images/                        Logo and documentation images
.github/workflows/                  Release ZIP workflow
```
