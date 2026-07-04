"""The Motorvärmare integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, PLATFORMS
from .coordinator import CarHeaterCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Motorvärmare from a config entry."""
    coordinator = CarHeaterCoordinator(hass, entry)
    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _minute_tick(now):
        hass.async_create_task(coordinator.async_request_refresh())

    # Run on second 0 each minute, instead of one minute after Home Assistant happened to set up the entry.
    entry.async_on_unload(async_track_time_change(hass, _minute_tick, second=0))
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
