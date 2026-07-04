"""Buttons for Motorvärmare."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant

from .const import DOMAIN, STATUS_RUNNING, STATUS_START_NOW
from .entity import CarHeaterEntity


BUTTONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(key="start_now", translation_key="start_now", icon="mdi:play-circle"),
    ButtonEntityDescription(key="stop_now", translation_key="stop_now", icon="mdi:stop-circle"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(CarHeaterButton(coordinator, entry, description) for description in BUTTONS)


class CarHeaterButton(CarHeaterEntity, ButtonEntity):
    """Motor heater button."""

    entity_description: ButtonEntityDescription

    def __init__(self, coordinator, entry: ConfigEntry, description: ButtonEntityDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if not super().available or self.coordinator.data is None:
            return False

        data = self.coordinator.data
        heater_is_on = data.heater_switch_state == STATE_ON
        running = data.status in {STATUS_RUNNING, STATUS_START_NOW} or heater_is_on

        if self.entity_description.key == "start_now":
            return not running
        if self.entity_description.key == "stop_now":
            return running
        return True

    async def async_press(self) -> None:
        if self.entity_description.key == "start_now":
            await self.coordinator.async_start_now()
        elif self.entity_description.key == "stop_now":
            await self.coordinator.async_stop_now()
