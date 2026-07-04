"""Config flow for Motorvärmare."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AFTER_DEPARTURE_MINUTES,
    CONF_COEFFICIENT,
    CONF_HEATER_SWITCH,
    CONF_MANUAL_DEPARTURE,
    CONF_MAX_RUNTIME,
    CONF_MIN_RUNTIME,
    CONF_OFFSET,
    CONF_POWER_SENSOR,
    CONF_TEMP_LIMIT,
    CONF_TEMP_SENSORS,
    CONF_WORKDAY_DEPARTURE,
    CONF_WORKDAY_SENSOR,
    CONF_USE_WORKDAY,
    DEFAULT_AFTER_DEPARTURE_MINUTES,
    DEFAULT_COEFFICIENT,
    DEFAULT_MANUAL_DEPARTURE,
    DEFAULT_USE_WORKDAY,
    DEFAULT_MAX_RUNTIME,
    DEFAULT_MIN_RUNTIME,
    DEFAULT_OFFSET,
    DEFAULT_TEMP_LIMIT,
    DEFAULT_WORKDAY_DEPARTURE,
    DOMAIN,
    NAME,
)


class CarHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Create the integration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            data = _clean_user_input(user_input)
            title = data.pop(CONF_NAME, NAME)
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return CarHeaterOptionsFlow(config_entry)


class CarHeaterOptionsFlow(config_entries.OptionsFlow):
    """Options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # Home Assistant Core newer versions expose config_entry as a read-only
        # property on OptionsFlow. Store our copy under a private name for
        # compatibility with both older and newer Core versions.
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=_clean_user_input(user_input, include_name=False))

        current = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(current, include_name=False),
        )


def _clean_user_input(user_input: dict[str, Any], include_name: bool = True) -> dict[str, Any]:
    data = dict(user_input)
    sensors = data.get(CONF_TEMP_SENSORS) or []
    if isinstance(sensors, str):
        sensors = [sensors] if sensors else []
    data[CONF_TEMP_SENSORS] = [str(sensor) for sensor in sensors if sensor]

    data[CONF_USE_WORKDAY] = bool(data.get(CONF_USE_WORKDAY, DEFAULT_USE_WORKDAY))

    if not data.get(CONF_WORKDAY_SENSOR):
        data.pop(CONF_WORKDAY_SENSOR, None)
    if not data.get(CONF_POWER_SENSOR):
        data.pop(CONF_POWER_SENSOR, None)

    if not include_name:
        data.pop(CONF_NAME, None)

    return data


def _schema(defaults: dict[str, Any] | None = None, include_name: bool = True) -> vol.Schema:
    defaults = defaults or {}

    fields: dict[Any, Any] = {}
    if include_name:
        fields[vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, NAME))] = str

    fields.update(
        {
            vol.Required(CONF_HEATER_SWITCH, default=defaults.get(CONF_HEATER_SWITCH)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="switch")
            ),
            vol.Required(CONF_USE_WORKDAY, default=defaults.get(CONF_USE_WORKDAY, DEFAULT_USE_WORKDAY)): selector.BooleanSelector(),
            vol.Optional(CONF_TEMP_SENSORS, default=defaults.get(CONF_TEMP_SENSORS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            ),
            vol.Optional(CONF_WORKDAY_SENSOR, default=defaults.get(CONF_WORKDAY_SENSOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Optional(CONF_POWER_SENSOR, default=defaults.get(CONF_POWER_SENSOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_WORKDAY_DEPARTURE, default=defaults.get(CONF_WORKDAY_DEPARTURE, DEFAULT_WORKDAY_DEPARTURE)): selector.TimeSelector(),
            vol.Required(CONF_MANUAL_DEPARTURE, default=defaults.get(CONF_MANUAL_DEPARTURE, DEFAULT_MANUAL_DEPARTURE)): selector.TimeSelector(),
            vol.Required(CONF_TEMP_LIMIT, default=defaults.get(CONF_TEMP_LIMIT, DEFAULT_TEMP_LIMIT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-30, max=20, step=0.5, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="°C")
            ),
            vol.Required(CONF_COEFFICIENT, default=defaults.get(CONF_COEFFICIENT, DEFAULT_COEFFICIENT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-1, max=1, step=0.01, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_OFFSET, default=defaults.get(CONF_OFFSET, DEFAULT_OFFSET)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="h")
            ),
            vol.Required(CONF_MIN_RUNTIME, default=defaults.get(CONF_MIN_RUNTIME, DEFAULT_MIN_RUNTIME)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="h")
            ),
            vol.Required(CONF_MAX_RUNTIME, default=defaults.get(CONF_MAX_RUNTIME, DEFAULT_MAX_RUNTIME)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="h")
            ),
            vol.Required(CONF_AFTER_DEPARTURE_MINUTES, default=defaults.get(CONF_AFTER_DEPARTURE_MINUTES, DEFAULT_AFTER_DEPARTURE_MINUTES)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=120, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="min")
            ),
        }
    )
    return vol.Schema(fields)
