"""Sensors for Motorvärmare."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
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
    SensorEntityDescription(key="runtime_curve", translation_key="runtime_curve", icon="mdi:chart-bell-curve"),
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
        if key == "runtime_curve":
            return data.runtime_mode
        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        attrs = _common_attributes(data)

        if self.entity_description.key == "runtime_curve":
            return {
                "mode": data.runtime_mode,
                "temperature_limit": data.runtime_temp_limit,
                "max_runtime_minutes": int(round((data.runtime_hours or 0.0) * 60)),
                "curve": data.runtime_curve or [],
                "curve_mode": data.runtime_curve_mode,
            }

        return attrs


def _common_attributes(data) -> dict:
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
        "heater_switch_entity_id": data.heater_switch_entity_id,
        "heater_switch_name": data.heater_switch_name,
        "heater_switch_state": data.heater_switch_state,
        "heater_switch_is_on": data.heater_switch_is_on,
        "heater_switch_available": data.heater_switch_available,
        "power_entity_id": data.power_entity_id,
        "power_name": data.power_name,
        "power": data.power,
        "power_unit": data.power_unit,
        "power_device_class": data.power_device_class,
        "schedule_mode": data.schedule_mode,
        "runtime_minutes": data.runtime_minutes,
        "runtime_mode": data.runtime_mode,
        "runtime_temp_limit": data.runtime_temp_limit,
        "runtime_curve": data.runtime_curve or [],
        "runtime_curve_mode": data.runtime_curve_mode,
        "after_departure_minutes": data.after_departure_minutes,
        "last_action": data.last_action,
        "last_start": data.last_start.isoformat() if data.last_start else None,
        "last_stop": data.last_stop.isoformat() if data.last_stop else None,
        "current_start": data.current_start.isoformat() if data.current_start else None,
        "current_stop": data.current_stop.isoformat() if data.current_stop else None,
        "current_duration_minutes": data.current_duration_minutes,
        "previous_start": data.previous_start.isoformat() if data.previous_start else None,
        "previous_stop": data.previous_stop.isoformat() if data.previous_stop else None,
        "previous_duration_minutes": data.previous_duration_minutes,
        "planned_start": data.planned_start.isoformat() if data.planned_start else None,
        "planned_stop": data.planned_stop.isoformat() if data.planned_stop else None,
        "planned_departure": data.planned_departure.isoformat() if data.planned_departure else None,
        "planned_duration_minutes": data.planned_duration_minutes,
        "run_history": data.run_history or [],
        "timeline": {
            "history": data.run_history or [],
            "previous": {
                "start": data.previous_start.isoformat() if data.previous_start else None,
                "stop": data.previous_stop.isoformat() if data.previous_stop else None,
                "duration_minutes": data.previous_duration_minutes,
            },
            "current": {
                "start": data.current_start.isoformat() if data.current_start else None,
                "stop": data.current_stop.isoformat() if data.current_stop else None,
                "duration_minutes": data.current_duration_minutes,
                "is_on": data.heater_switch_is_on,
            },
            "planned": {
                "start": data.planned_start.isoformat() if data.planned_start else None,
                "stop": data.planned_stop.isoformat() if data.planned_stop else None,
                "departure": data.planned_departure.isoformat() if data.planned_departure else None,
                "duration_minutes": data.planned_duration_minutes,
            },
        },
        "heater_switch": {
            "entity_id": data.heater_switch_entity_id,
            "name": data.heater_switch_name,
            "state": data.heater_switch_state,
            "is_on": data.heater_switch_is_on,
            "available": data.heater_switch_available,
        },
        "temperature": {
            "entity_id": data.temperature_source,
            "name": data.temperature_source_name,
            "value": data.temperature,
            "unit": "°C",
        },
        "runtime": {
            "minutes": data.runtime_minutes,
            "hours": data.runtime_hours,
            "mode": data.runtime_mode,
            "temperature_limit": data.runtime_temp_limit,
            "curve": data.runtime_curve or [],
            "curve_mode": data.runtime_curve_mode,
        },
        "power_sensor": {
            "entity_id": data.power_entity_id,
            "name": data.power_name,
            "value": data.power,
            "unit": data.power_unit,
            "device_class": data.power_device_class,
        },
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
