"""Switches for Motorvärmare."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import CarHeaterEntity


SWITCHES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(key="enabled", translation_key="enabled", icon="mdi:car-defrost-front"),
    SwitchEntityDescription(key="manual_active", translation_key="manual_active", icon="mdi:car-clock"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(CarHeaterSwitch(coordinator, entry, description) for description in SWITCHES)


class CarHeaterSwitch(CarHeaterEntity, SwitchEntity):
    """Motor heater switch."""

    entity_description: SwitchEntityDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: SwitchEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        if self.entity_description.key == "enabled":
            return data.enabled
        if self.entity_description.key == "manual_active":
            return data.manual_active
        return False

    async def async_turn_on(self, **kwargs) -> None:
        if self.entity_description.key == "enabled":
            await self.coordinator.async_set_enabled(True)
        elif self.entity_description.key == "manual_active":
            await self.coordinator.async_set_manual_active(True)

    async def async_turn_off(self, **kwargs) -> None:
        if self.entity_description.key == "enabled":
            await self.coordinator.async_set_enabled(False)
        elif self.entity_description.key == "manual_active":
            await self.coordinator.async_set_manual_active(False)
