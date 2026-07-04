"""Sensors for Motorvärmare."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import CarHeaterEntity


SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key="departure", translation_key="departure", icon="mdi:clock"),
    SensorEntityDescription(key="start", translation_key="start", icon="mdi:clock-start"),
    SensorEntityDescription(key="stop", translation_key="stop", icon="mdi:clock-end"),
    SensorEntityDescription(key="runtime", translation_key="runtime", icon="mdi:timer-outline"),
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(key="temperature_source", translation_key="temperature_source", icon="mdi:thermometer-lines"),
    SensorEntityDescription(key="status", translation_key="status", icon="mdi:car-clock"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(CarHeaterSensor(coordinator, entry, description) for description in SENSORS)


class CarHeaterSensor(CarHeaterEntity, SensorEntity):
    """Motor heater sensor."""

    entity_description: SensorEntityDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: SensorEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        data = self.coordinator.data
        key = self.entity_description.key

        if key == "departure":
            return _fmt_dt(data.departure)
        if key == "start":
            return _fmt_dt(data.start) if data.start else "Aldrig"
        if key == "stop":
            return _fmt_dt(data.stop)
        if key == "runtime":
            return _fmt_runtime(data.runtime_hours)
        if key == "temperature":
            return data.temperature
        if key == "temperature_source":
            return data.temperature_source_name or data.temperature_source or "Ingen"
        if key == "status":
            return data.status
        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "enabled": data.enabled,
            "manual_active": data.manual_active,
            "is_workday": data.is_workday,
            "runtime_hours": data.runtime_hours,
            "temperature_source": data.temperature_source,
            "temperature_source_name": data.temperature_source_name,
            "departure_datetime": data.departure.isoformat() if data.departure else None,
            "start_datetime": data.start.isoformat() if data.start else None,
            "stop_datetime": data.stop.isoformat() if data.stop else None,
            "heater_switch_state": data.heater_switch_state,
            "last_action": data.last_action,
        }


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "--:--"
    return value.strftime("%H:%M")


def _fmt_runtime(hours: float | None) -> str:
    if not hours or hours <= 0:
        return "00:00"
    seconds = int(round(hours * 3600))
    td = timedelta(seconds=seconds)
    total_minutes = int(td.total_seconds() // 60)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
