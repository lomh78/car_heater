"""Date selector for the one-time departure."""
from __future__ import annotations
from datetime import date
from homeassistant.components.date import DateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from .const import DOMAIN
from .entity import CarHeaterEntity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([CarHeaterDepartureDate(hass.data[DOMAIN][entry.entry_id], entry)])

class CarHeaterDepartureDate(CarHeaterEntity, DateEntity):
    _attr_translation_key = "manual_date"
    _attr_icon = "mdi:calendar-clock"
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "manual_date")
    @property
    def native_value(self) -> date:
        try:
            return date.fromisoformat(self.coordinator.manual_date)
        except (TypeError, ValueError):
            return dt_util.now().date()
    async def async_set_value(self, value: date) -> None:
        await self.coordinator.async_set_manual_date(value)
