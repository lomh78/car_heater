"""Coordinator and calculation logic for Motorvärmare."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AFTER_DEPARTURE_MINUTES,
    CONF_HEATER_SWITCH,
    CONF_MANUAL_DEPARTURE,
    CONF_MAX_RUNTIME,
    CONF_MANUAL_RUNTIME,
    CONF_POWER_SENSOR,
    CONF_TEMP_LIMIT,
    CONF_TEMP_SENSORS,
    CONF_WORKDAY_DEPARTURE,
    CONF_WORKDAY_SENSOR,
    CONF_USE_WORKDAY,
    DEFAULT_AFTER_DEPARTURE_MINUTES,
    DEFAULT_MANUAL_DEPARTURE,
    DEFAULT_USE_WORKDAY,
    DEFAULT_AUTO_RUNTIME_CURVE,
    DEFAULT_MANUAL_RUNTIME_CURVE,
    MANUAL_RUNTIME_CURVE_FIELDS,
    DEFAULT_MAX_RUNTIME,
    DEFAULT_MANUAL_RUNTIME,
    DEFAULT_TEMP_LIMIT,
    DEFAULT_WORKDAY_DEPARTURE,
    DOMAIN,
    STATE_ENABLED,
    STATE_MANUAL_ACTIVE,
    STATE_START_NOW_ACTIVE,
    STATE_START_NOW_STARTED,
    STATE_START_NOW_STOP,
    STATE_LAST_START,
    STATE_LAST_STOP,
    STATE_CURRENT_START,
    STATE_CURRENT_STOP,
    STATE_PREVIOUS_START,
    STATE_PREVIOUS_STOP,
    STATE_RUN_HISTORY,
    DEFAULT_RUN_HISTORY_LIMIT,
    STATUS_DISABLED,
    STATUS_FINISHED,
    STATUS_NO_DEPARTURE,
    STATUS_NO_HEATING_NEEDED,
    STATUS_NO_TEMPERATURE,
    STATUS_RUNNING,
    STATUS_START_NOW,
    STATUS_WAITING,
    STORE_KEY,
    STORE_VERSION,
)

_LOGGER = logging.getLogger(__name__)
BAD_STATES = {STATE_UNAVAILABLE, STATE_UNKNOWN, "", None}


@dataclass(slots=True)
class HeaterData:
    """Calculated state for the heater."""

    enabled: bool = False
    manual_active: bool = False
    start_now_active: bool = False
    is_workday: bool | None = None
    temperature: float | None = None
    temperature_source: str | None = None
    temperature_source_name: str | None = None
    runtime_hours: float = 0.0
    departure: datetime | None = None
    start: datetime | None = None
    stop: datetime | None = None
    status: str = STATUS_DISABLED
    heater_switch_entity_id: str | None = None
    heater_switch_name: str | None = None
    heater_switch_state: str | None = None
    heater_switch_is_on: bool = False
    heater_switch_available: bool = False
    power_entity_id: str | None = None
    power_name: str | None = None
    power: float | None = None
    power_unit: str | None = None
    power_device_class: str | None = None
    schedule_mode: str = "none"
    planned_start: datetime | None = None
    planned_stop: datetime | None = None
    planned_departure: datetime | None = None
    last_action: str | None = None
    last_start: datetime | None = None
    last_stop: datetime | None = None
    current_start: datetime | None = None
    current_stop: datetime | None = None
    previous_start: datetime | None = None
    previous_stop: datetime | None = None
    runtime_minutes: int = 0
    runtime_mode: str = "auto"
    runtime_curve: list[dict[str, Any]] | None = None
    runtime_temp_limit: float = DEFAULT_TEMP_LIMIT
    runtime_curve_mode: str = "auto"
    after_departure_minutes: int = 0
    previous_duration_minutes: int | None = None
    current_duration_minutes: int | None = None
    planned_duration_minutes: int | None = None
    run_history: list[dict[str, Any]] | None = None


class CarHeaterCoordinator(DataUpdateCoordinator[HeaterData]):
    """Calculate motor heater state and control the selected switch."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        self.store: Store[dict[str, Any]] = Store(
            hass,
            STORE_VERSION,
            f"{DOMAIN}.{entry.entry_id}.{STORE_KEY}",
        )
        self.enabled = False
        self.manual_active = False
        self.start_now_active = False
        self.start_now_started: str | None = None
        self.start_now_stop: str | None = None
        self.last_action: str | None = None
        self.last_start: str | None = None
        self.last_stop: str | None = None
        self.current_start: str | None = None
        self.current_stop: str | None = None
        self.previous_start: str | None = None
        self.previous_stop: str | None = None
        self.run_history: list[dict[str, Any]] = []
        self._previous_status: str | None = None

    @property
    def config(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    @property
    def heater_switch(self) -> str:
        return str(self.config[CONF_HEATER_SWITCH])

    @property
    def use_workday(self) -> bool:
        return bool(self.config.get(CONF_USE_WORKDAY, DEFAULT_USE_WORKDAY))

    async def async_load(self) -> None:
        stored = await self.store.async_load()
        if stored:
            self.enabled = bool(stored.get(STATE_ENABLED, False))
            self.manual_active = bool(stored.get(STATE_MANUAL_ACTIVE, False))
            self.start_now_active = bool(stored.get(STATE_START_NOW_ACTIVE, False))
            self.start_now_started = stored.get(STATE_START_NOW_STARTED)
            self.start_now_stop = stored.get(STATE_START_NOW_STOP)
            self.last_start = stored.get(STATE_LAST_START)
            self.last_stop = stored.get(STATE_LAST_STOP)
            self.current_start = stored.get(STATE_CURRENT_START)
            self.current_stop = stored.get(STATE_CURRENT_STOP)
            self.previous_start = stored.get(STATE_PREVIOUS_START)
            self.previous_stop = stored.get(STATE_PREVIOUS_STOP)
            history = stored.get(STATE_RUN_HISTORY, [])
            self.run_history = history if isinstance(history, list) else []

    async def _async_save(self) -> None:
        await self.store.async_save(
            {
                STATE_ENABLED: self.enabled,
                STATE_MANUAL_ACTIVE: self.manual_active,
                STATE_START_NOW_ACTIVE: self.start_now_active,
                STATE_START_NOW_STARTED: self.start_now_started,
                STATE_START_NOW_STOP: self.start_now_stop,
                STATE_LAST_START: self.last_start,
                STATE_LAST_STOP: self.last_stop,
                STATE_CURRENT_START: self.current_start,
                STATE_CURRENT_STOP: self.current_stop,
                STATE_PREVIOUS_START: self.previous_start,
                STATE_PREVIOUS_STOP: self.previous_stop,
                STATE_RUN_HISTORY: self.run_history[-DEFAULT_RUN_HISTORY_LIMIT:],
            }
        )

    async def async_set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        await self._async_save()
        await self.async_request_refresh()

    async def async_set_manual_active(self, active: bool) -> None:
        self.manual_active = active
        if active:
            self.enabled = True
        await self._async_save()
        await self.async_request_refresh()

    async def async_start_now(self) -> None:
        """Start immediately and stop after calculated runtime plus after-time."""
        now = dt_util.now().replace(second=0, microsecond=0)
        temperature, _, _ = self._first_valid_temperature()
        runtime = self._runtime_from_temperature(temperature)
        after_minutes = int(self.config.get(CONF_AFTER_DEPARTURE_MINUTES, DEFAULT_AFTER_DEPARTURE_MINUTES))
        stop = now + timedelta(hours=runtime, minutes=after_minutes)
        if stop <= now:
            stop = now + timedelta(minutes=max(after_minutes, 1))

        self.start_now_active = True
        self.enabled = True
        self.start_now_started = now.isoformat()
        self.start_now_stop = stop.isoformat()
        self.current_start = now.isoformat()
        self.current_stop = None
        self.last_start = now.isoformat()
        self.last_stop = None
        await self._async_save()
        await self.async_request_refresh()

    def _add_run_to_history(self, start: str | None, stop: str | None, source: str = "auto") -> None:
        """Store a completed run for timeline/history rendering."""
        if not start or not stop:
            return

        start_dt = self._parse_dt(start)
        stop_dt = self._parse_dt(stop)
        duration = self._duration_minutes(start_dt, stop_dt)
        if duration is None or duration <= 0:
            return

        item = {
            "start": start,
            "stop": stop,
            "duration_minutes": duration,
            "source": source,
        }

        # Remove duplicates for the same run, then keep the newest completed runs.
        self.run_history = [
            run for run in self.run_history
            if not (run.get("start") == start and run.get("stop") == stop)
        ]
        self.run_history.append(item)
        self.run_history = self.run_history[-DEFAULT_RUN_HISTORY_LIMIT:]

    async def async_stop_now(self) -> None:
        """Stop the heater and clear immediate/manual run modes."""
        self.start_now_active = False
        self.manual_active = False
        self.start_now_started = None
        self.start_now_stop = None
        stop_time = dt_util.now().replace(microsecond=0).isoformat()
        self.current_stop = stop_time
        if self.current_start:
            self.previous_start = self.current_start
            self.previous_stop = stop_time
            self._add_run_to_history(self.current_start, stop_time, "auto")
            self._add_run_to_history(self.current_start, stop_time, "manual_stop")
        self.last_stop = stop_time
        await self._async_turn_heater_off()
        self.current_start = None
        self.current_stop = None
        await self._async_save()
        await self.async_request_refresh()

    async def async_set_time(self, key: str, value: time) -> None:
        options = dict(self.entry.options)
        options[key] = value.strftime("%H:%M")
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        await self.async_request_refresh()

    async def _async_update_data(self) -> HeaterData:
        data = self._calculate(dt_util.now())
        await self._control_switch(data)
        self._previous_status = data.status
        return data

    def _get_time(self, key: str, default: str) -> time:
        value = self.config.get(key, default)
        try:
            hour, minute = str(value).split(":")[:2]
            return time(int(hour), int(minute))
        except (TypeError, ValueError):
            hour, minute = default.split(":")[:2]
            return time(int(hour), int(minute))

    def _get_temperature_sensors(self) -> list[str]:
        value = self.config.get(CONF_TEMP_SENSORS, [])
        if isinstance(value, str):
            return [value] if value else []
        return [str(item) for item in value or [] if item]

    def _first_valid_temperature(self) -> tuple[float | None, str | None, str | None]:
        for entity_id in self._get_temperature_sensors():
            state = self.hass.states.get(entity_id)
            if state is None or state.state in BAD_STATES:
                continue
            try:
                return float(state.state), entity_id, state.name
            except (TypeError, ValueError):
                continue
        return None, None, None

    def _current_power(self) -> tuple[float | None, str | None, str | None, str | None, str | None]:
        entity_id = self.config.get(CONF_POWER_SENSOR)
        if not entity_id:
            return None, None, None, None, None
        state = self.hass.states.get(str(entity_id))
        if state is None:
            return None, str(entity_id), None, None, None

        unit = state.attributes.get("unit_of_measurement")
        device_class = state.attributes.get("device_class")
        if state.state in BAD_STATES:
            return None, str(entity_id), state.name, unit, device_class
        try:
            return float(state.state), str(entity_id), state.name, unit, device_class
        except (TypeError, ValueError):
            return None, str(entity_id), state.name, unit, device_class

    def _is_manual_runtime(self) -> bool:
        return bool(self.config.get(CONF_MANUAL_RUNTIME, DEFAULT_MANUAL_RUNTIME))

    def _runtime_curve_points(self) -> tuple[tuple[float, float], ...]:
        """Return the active runtime curve as (degrees below limit, minutes)."""
        if not self._is_manual_runtime():
            return tuple((float(delta), float(minutes)) for delta, minutes in DEFAULT_AUTO_RUNTIME_CURVE)

        points: list[tuple[float, float]] = []
        for key, delta, default_minutes in MANUAL_RUNTIME_CURVE_FIELDS:
            try:
                minutes = float(self.config.get(key, default_minutes))
            except (TypeError, ValueError):
                minutes = float(default_minutes)
            points.append((float(delta), max(minutes, 0.0)))
        return tuple(points)

    def _runtime_curve_preview(self, temp_limit: float | None = None) -> list[dict[str, Any]]:
        """Return active curve as absolute temperatures for UI/card preview."""
        limit = float(temp_limit if temp_limit is not None else self.config.get(CONF_TEMP_LIMIT, DEFAULT_TEMP_LIMIT))
        return [
            {
                "temperature": round(limit - diff, 1),
                "degrees_below_limit": round(diff, 1),
                "runtime_minutes": int(round(minutes)),
            }
            for diff, minutes in self._runtime_curve_points()
        ]

    @staticmethod
    def _interpolate_curve(delta: float, points: tuple[tuple[float, float], ...]) -> float:
        """Interpolate runtime minutes from configured curve points."""
        if not points:
            return 0.0
        points = tuple(sorted(points, key=lambda item: item[0]))
        if delta <= points[0][0]:
            return float(points[0][1])

        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            if delta <= x2:
                if x2 == x1:
                    return float(y2)
                ratio = (delta - x1) / (x2 - x1)
                return float(y1 + ratio * (y2 - y1))

        # Extrapolate beyond the last point using the last segment. The final
        # value is still clamped by max_runtime below.
        if len(points) == 1:
            return float(points[0][1])
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        ratio = (delta - x1) / (x2 - x1)
        return float(y1 + ratio * (y2 - y1))

    def _runtime_from_temperature(self, temperature: float | None) -> float:
        if temperature is None:
            return 0.0

        temp_limit = float(self.config.get(CONF_TEMP_LIMIT, DEFAULT_TEMP_LIMIT))
        if temperature >= temp_limit:
            return 0.0

        # The curve is defined as degrees below the configured limit. Moving the
        # temperature limit therefore shifts the curve without changing its shape.
        runtime_minutes = self._interpolate_curve(temp_limit - temperature, self._runtime_curve_points())

        max_minutes = float(self.config.get(CONF_MAX_RUNTIME, DEFAULT_MAX_RUNTIME)) * 60
        min_minutes = 0.0
        runtime_minutes = max(runtime_minutes, min_minutes)
        runtime_minutes = min(runtime_minutes, max_minutes)
        return round(runtime_minutes / 60, 2)

    def _is_workday(self) -> bool | None:
        entity_id = self.config.get(CONF_WORKDAY_SENSOR)
        if not entity_id:
            return None
        state = self.hass.states.get(str(entity_id))
        if state is None or state.state in BAD_STATES:
            return None
        return state.state == STATE_ON

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _duration_minutes(start: datetime | None, stop: datetime | None) -> int | None:
        if start is None or stop is None or stop < start:
            return None
        return int((stop - start).total_seconds() // 60)

    def _set_timeline_durations(self, data: HeaterData, now: datetime) -> None:
        data.runtime_minutes = int(round((data.runtime_hours or 0.0) * 60))
        data.runtime_mode = "manual" if self._is_manual_runtime() else "auto"
        data.runtime_temp_limit = float(self.config.get(CONF_TEMP_LIMIT, DEFAULT_TEMP_LIMIT))
        data.runtime_curve_mode = data.runtime_mode
        data.runtime_curve = self._runtime_curve_preview(data.runtime_temp_limit)
        data.after_departure_minutes = int(
            self.config.get(CONF_AFTER_DEPARTURE_MINUTES, DEFAULT_AFTER_DEPARTURE_MINUTES)
        )
        data.previous_duration_minutes = self._duration_minutes(data.previous_start, data.previous_stop)
        current_end = data.current_stop or (now if data.heater_switch_is_on else None)
        data.current_duration_minutes = self._duration_minutes(data.current_start, current_end)
        data.planned_duration_minutes = self._duration_minutes(data.planned_start, data.planned_stop)

    def _departure_datetime(self, departure_time: time, now: datetime, *, roll_to_tomorrow_after_stop: bool) -> datetime:
        departure = datetime.combine(now.date(), departure_time, tzinfo=now.tzinfo)
        stop = departure + timedelta(
            minutes=int(self.config.get(CONF_AFTER_DEPARTURE_MINUTES, DEFAULT_AFTER_DEPARTURE_MINUTES))
        )
        if roll_to_tomorrow_after_stop and now > stop:
            departure += timedelta(days=1)
        return departure

    def _calculate(self, now: datetime) -> HeaterData:
        temperature, source, source_name = self._first_valid_temperature()
        runtime = self._runtime_from_temperature(temperature)
        is_workday = self._is_workday() if self.use_workday else None
        switch_state = self.hass.states.get(self.heater_switch)
        power, power_entity_id, power_name, power_unit, power_device_class = self._current_power()

        base = HeaterData(
            enabled=self.enabled,
            manual_active=self.manual_active,
            start_now_active=self.start_now_active,
            is_workday=is_workday,
            temperature=temperature,
            temperature_source=source,
            temperature_source_name=source_name,
            runtime_hours=runtime,
            heater_switch_entity_id=self.heater_switch,
            heater_switch_name=switch_state.name if switch_state else self.heater_switch,
            heater_switch_state=switch_state.state if switch_state else None,
            heater_switch_is_on=switch_state is not None and switch_state.state == STATE_ON,
            heater_switch_available=switch_state is not None and switch_state.state not in BAD_STATES,
            power_entity_id=power_entity_id,
            power_name=power_name,
            power=power,
            power_unit=power_unit,
            power_device_class=power_device_class,
            last_action=self.last_action,
            last_start=self._parse_dt(self.last_start),
            last_stop=self._parse_dt(self.last_stop),
            current_start=self._parse_dt(self.current_start),
            current_stop=self._parse_dt(self.current_stop),
            previous_start=self._parse_dt(self.previous_start),
            previous_stop=self._parse_dt(self.previous_stop),
            run_history=list(self.run_history),
        )

        if not self.enabled:
            base.status = STATUS_DISABLED
            self._set_timeline_durations(base, now)
            return base

        if self.start_now_active:
            started = self._parse_dt(self.start_now_started)
            stop = self._parse_dt(self.start_now_stop)
            if started is None or stop is None:
                self.start_now_active = False
                base.start_now_active = False
                base.status = STATUS_DISABLED
                self._set_timeline_durations(base, now)
                return base

            base.schedule_mode = "start_now"
            base.start = started
            base.planned_start = started
            base.departure = stop - timedelta(
                minutes=int(self.config.get(CONF_AFTER_DEPARTURE_MINUTES, DEFAULT_AFTER_DEPARTURE_MINUTES))
            )
            base.stop = stop
            base.planned_stop = stop
            base.planned_departure = base.departure
            base.status = STATUS_START_NOW if now < stop else STATUS_FINISHED
            self._set_timeline_durations(base, now)
            return base

        roll_to_tomorrow = True
        if self.manual_active:
            departure_time = self._get_time(CONF_MANUAL_DEPARTURE, DEFAULT_MANUAL_DEPARTURE)
            # Treat manual departure the same way as scheduled departures:
            # if today's manual departure and after-time have already passed,
            # keep one-time mode active and schedule it for tomorrow instead
            # of immediately marking it as finished and turning it off.
            roll_to_tomorrow = True
            base.schedule_mode = "manual"
        elif self.use_workday and is_workday is True:
            departure_time = self._get_time(CONF_WORKDAY_DEPARTURE, DEFAULT_WORKDAY_DEPARTURE)
            base.schedule_mode = "workday"
        else:
            base.status = STATUS_NO_DEPARTURE
            self._set_timeline_durations(base, now)
            return base

        departure = self._departure_datetime(
            departure_time,
            now,
            roll_to_tomorrow_after_stop=roll_to_tomorrow,
        )
        start = departure - timedelta(hours=runtime) if runtime > 0 else None
        stop = departure + timedelta(
            minutes=int(self.config.get(CONF_AFTER_DEPARTURE_MINUTES, DEFAULT_AFTER_DEPARTURE_MINUTES))
        )

        if temperature is None:
            status = STATUS_NO_TEMPERATURE
        elif runtime <= 0:
            status = STATUS_NO_HEATING_NEEDED
        elif start is not None and start <= now < stop:
            status = STATUS_RUNNING
        elif now >= stop:
            status = STATUS_FINISHED
        else:
            status = STATUS_WAITING

        base.departure = departure
        base.start = start
        base.stop = stop
        base.planned_start = start
        base.planned_stop = stop
        base.planned_departure = departure
        base.status = status
        self._set_timeline_durations(base, now)
        return base

    async def _async_track_physical_switch(self, is_on: bool) -> bool:
        """Track actual switch state transitions, including manual changes outside this integration."""
        changed = False
        now_iso = dt_util.now().replace(microsecond=0).isoformat()

        if is_on and not self.current_start:
            self.current_start = now_iso
            self.current_stop = None
            self.last_start = now_iso
            self.last_stop = None
            changed = True

        if not is_on and self.current_start:
            self.current_stop = now_iso
            self.previous_start = self.current_start
            self.previous_stop = now_iso
            self._add_run_to_history(self.current_start, now_iso, "switch")
            self.last_stop = now_iso
            self.current_start = None
            self.current_stop = None
            changed = True

        if changed:
            await self._async_save()
        return changed

    async def _async_turn_heater_off(self) -> None:
        stop_time = dt_util.now().replace(microsecond=0).isoformat()
        self.current_stop = stop_time
        if self.current_start:
            self.previous_start = self.current_start
            self.previous_stop = stop_time
            self._add_run_to_history(self.current_start, stop_time, "auto")
            self._add_run_to_history(self.current_start, stop_time, "manual_stop")
        self.last_stop = stop_time
        await self.hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": self.heater_switch},
            blocking=False,
        )
        self.last_action = "turn_off"
        self.current_start = None
        self.current_stop = None

    async def _control_switch(self, data: HeaterData) -> None:
        switch_state = self.hass.states.get(self.heater_switch)
        is_on = switch_state is not None and switch_state.state == STATE_ON
        should_be_on = data.enabled and data.status in {STATUS_RUNNING, STATUS_START_NOW} and data.runtime_hours >= 0

        # Keep timeline state in sync with the real switch, even if it was toggled manually.
        if not should_be_on or is_on:
            if await self._async_track_physical_switch(is_on):
                data.current_start = self._parse_dt(self.current_start)
                data.current_stop = self._parse_dt(self.current_stop)
                data.previous_start = self._parse_dt(self.previous_start)
                data.previous_stop = self._parse_dt(self.previous_stop)
                data.last_start = self._parse_dt(self.last_start)
                data.last_stop = self._parse_dt(self.last_stop)
                self._set_timeline_durations(data, dt_util.now())

        if should_be_on and not is_on:
            start_time = dt_util.now().replace(microsecond=0).isoformat()
            self.current_start = start_time
            self.current_stop = None
            self.last_start = start_time
            self.last_stop = None
            data.current_start = self._parse_dt(self.current_start)
            data.current_stop = None
            data.last_start = self._parse_dt(self.last_start)
            data.last_stop = None
            await self.hass.services.async_call(
                "switch",
                "turn_on",
                {"entity_id": self.heater_switch},
                blocking=False,
            )
            self.last_action = "turn_on"
            data.last_action = self.last_action
            data.heater_switch_state = STATE_ON
            data.heater_switch_is_on = True
            data.heater_switch_available = True
            await self._async_save()
            return

        if not should_be_on and is_on and self._previous_status in {STATUS_RUNNING, STATUS_START_NOW}:
            await self._async_turn_heater_off()
            data.last_stop = self._parse_dt(self.last_stop)
            data.current_start = self._parse_dt(self.current_start)
            data.current_stop = self._parse_dt(self.current_stop)
            data.previous_start = self._parse_dt(self.previous_start)
            data.previous_stop = self._parse_dt(self.previous_stop)
            data.last_action = self.last_action
            data.heater_switch_state = "off"
            data.heater_switch_is_on = False
            data.heater_switch_available = True
            await self._async_save()

        if data.status == STATUS_FINISHED:
            changed = False
            if self.manual_active:
                self.manual_active = False
                data.manual_active = False
                changed = True
            if self.start_now_active:
                self.start_now_active = False
                self.start_now_started = None
                self.start_now_stop = None
                data.start_now_active = False
                changed = True
            if changed:
                await self._async_save()
