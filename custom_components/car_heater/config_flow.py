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
    CONF_HEATER_SWITCH,
    CONF_MANUAL_DEPARTURE,
    CONF_MANUAL_RUNTIME,
    CONF_MAX_RUNTIME,
    CONF_POWER_SENSOR,
    CONF_TEMP_LIMIT,
    CONF_TEMP_SENSORS,
    CONF_WORKDAY_DEPARTURE,
    CONF_WORKDAY_SENSOR,
    CONF_USE_WORKDAY,
    DEFAULT_AFTER_DEPARTURE_MINUTES,
    DEFAULT_MANUAL_DEPARTURE,
    DEFAULT_MANUAL_RUNTIME,
    DEFAULT_MAX_RUNTIME,
    DEFAULT_TEMP_LIMIT,
    DEFAULT_USE_WORKDAY,
    DEFAULT_WORKDAY_DEPARTURE,
    DOMAIN,
    MANUAL_RUNTIME_CURVE_FIELDS,
    NAME,
)


class CarHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending_data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Create the integration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _clean_user_input(user_input)
            self._pending_data = data
            if data.get(CONF_MANUAL_RUNTIME, DEFAULT_MANUAL_RUNTIME):
                return await self.async_step_manual_curve()

            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            title = data.pop(CONF_NAME, NAME)
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_main_schema(),
            errors=errors,
        )

    async def async_step_manual_curve(self, user_input: dict[str, Any] | None = None):
        """Configure a manual runtime curve during setup."""
        if user_input is not None:
            data = {**self._pending_data, **_clean_curve_input(user_input)}
            data[CONF_MANUAL_RUNTIME] = True
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            title = data.pop(CONF_NAME, NAME)
            return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="manual_curve",
            data_schema=_manual_curve_schema(self._pending_data),
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
        self._pending_options: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        current = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            data = _clean_user_input(user_input, include_name=False)
            self._pending_options = {**current, **data}
            if data.get(CONF_MANUAL_RUNTIME, DEFAULT_MANUAL_RUNTIME):
                return await self.async_step_manual_curve()
            return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="init",
            data_schema=_main_schema(current, include_name=False),
        )

    async def async_step_manual_curve(self, user_input: dict[str, Any] | None = None):
        """Configure manual runtime curve in options."""
        if user_input is not None:
            data = {**self._pending_options, **_clean_curve_input(user_input)}
            # Only store options, not the config entry title/name.
            data.pop(CONF_NAME, None)
            data[CONF_MANUAL_RUNTIME] = True
            return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="manual_curve",
            data_schema=_manual_curve_schema(self._pending_options),
        )


def _clean_user_input(user_input: dict[str, Any], include_name: bool = True) -> dict[str, Any]:
    data = dict(user_input)
    sensors = data.get(CONF_TEMP_SENSORS) or []
    if isinstance(sensors, str):
        sensors = [sensors] if sensors else []
    data[CONF_TEMP_SENSORS] = [str(sensor) for sensor in sensors if sensor]

    data[CONF_USE_WORKDAY] = bool(data.get(CONF_USE_WORKDAY, DEFAULT_USE_WORKDAY))
    data[CONF_MANUAL_RUNTIME] = bool(data.get(CONF_MANUAL_RUNTIME, DEFAULT_MANUAL_RUNTIME))

    if not data.get(CONF_WORKDAY_SENSOR):
        data.pop(CONF_WORKDAY_SENSOR, None)
    if not data.get(CONF_POWER_SENSOR):
        data.pop(CONF_POWER_SENSOR, None)

    if not include_name:
        data.pop(CONF_NAME, None)

    return data


def _clean_curve_input(user_input: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, _delta, default_minutes in MANUAL_RUNTIME_CURVE_FIELDS:
        try:
            data[key] = int(round(float(user_input.get(key, default_minutes))))
        except (TypeError, ValueError):
            data[key] = int(default_minutes)
    return data


def _main_schema(defaults: dict[str, Any] | None = None, include_name: bool = True) -> vol.Schema:
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
            vol.Required(CONF_MANUAL_RUNTIME, default=defaults.get(CONF_MANUAL_RUNTIME, DEFAULT_MANUAL_RUNTIME)): selector.BooleanSelector(),
            vol.Required(CONF_TEMP_LIMIT, default=defaults.get(CONF_TEMP_LIMIT, DEFAULT_TEMP_LIMIT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-30, max=25, step=0.5, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="°C")
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


def _manual_curve_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    fields: dict[Any, Any] = {}
    for key, _delta, default_minutes in MANUAL_RUNTIME_CURVE_FIELDS:
        fields[
            vol.Required(key, default=defaults.get(key, default_minutes))
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=600,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="min",
            )
        )
    return vol.Schema(fields)
