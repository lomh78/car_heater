"""Time entities for Motorvärmare."""
from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MANUAL_DEPARTURE,
    CONF_WORKDAY_DEPARTURE,
    DEFAULT_MANUAL_DEPARTURE,
    DEFAULT_WORKDAY_DEPARTURE,
    DOMAIN,
)
from .entity import CarHeaterEntity


TIMES: tuple[TimeEntityDescription, ...] = (
    TimeEntityDescription(key=CONF_WORKDAY_DEPARTURE, translation_key="workday_departure", icon="mdi:briefcase-clock"),
    TimeEntityDescription(key=CONF_MANUAL_DEPARTURE, translation_key="manual_departure", icon="mdi:clock-edit-outline"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up time entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for description in TIMES:
        if description.key == CONF_WORKDAY_DEPARTURE and not coordinator.use_workday:
            continue
        entities.append(CarHeaterTime(coordinator, entry, description))
    async_add_entities(entities)


class CarHeaterTime(CarHeaterEntity, TimeEntity):
    """Departure time setting."""

    entity_description: TimeEntityDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: TimeEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> time:
        default = DEFAULT_WORKDAY_DEPARTURE if self.entity_description.key == CONF_WORKDAY_DEPARTURE else DEFAULT_MANUAL_DEPARTURE
        value = self.coordinator.config.get(self.entity_description.key, default)
        try:
            hour, minute = str(value).split(":")[:2]
            return time(int(hour), int(minute))
        except (TypeError, ValueError):
            hour, minute = default.split(":")[:2]
            return time(int(hour), int(minute))

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_time(self.entity_description.key, value)
