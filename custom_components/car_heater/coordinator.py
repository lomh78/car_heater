"""Constants for the Car Heater integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "car_heater"
NAME = "Car Heater"
MANUFACTURER = "Custom"
VERSION = "1.0.10"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.TIME, Platform.BUTTON]

CONF_HEATER_SWITCH = "heater_switch"
CONF_TEMP_SENSORS = "temp_sensors"
CONF_WORKDAY_SENSOR = "workday_sensor"
CONF_POWER_SENSOR = "power_sensor"
CONF_USE_WORKDAY = "use_workday"
CONF_WORKDAY_DEPARTURE = "workday_departure"
CONF_MANUAL_DEPARTURE = "manual_departure"
CONF_TEMP_LIMIT = "temp_limit"
CONF_COEFFICIENT = "coefficient"
CONF_OFFSET = "offset"
CONF_MIN_RUNTIME = "min_runtime"
CONF_MAX_RUNTIME = "max_runtime"
CONF_AFTER_DEPARTURE_MINUTES = "after_departure_minutes"

DEFAULT_WORKDAY_DEPARTURE = "07:00"
DEFAULT_MANUAL_DEPARTURE = "07:00"
DEFAULT_USE_WORKDAY = True
DEFAULT_TEMP_LIMIT = 10.0
DEFAULT_COEFFICIENT = -0.08
DEFAULT_OFFSET = 1.3
DEFAULT_MIN_RUNTIME = 0.0
DEFAULT_MAX_RUNTIME = 4.0
DEFAULT_AFTER_DEPARTURE_MINUTES = 10
DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)

STORE_VERSION = 2
STORE_KEY = "runtime"

STATE_ENABLED = "enabled"
STATE_MANUAL_ACTIVE = "manual_active"
STATE_START_NOW_ACTIVE = "start_now_active"
STATE_START_NOW_STARTED = "start_now_started"
STATE_START_NOW_STOP = "start_now_stop"
STATE_LAST_START = "last_start"
STATE_LAST_STOP = "last_stop"
STATE_CURRENT_START = "current_start"
STATE_CURRENT_STOP = "current_stop"
STATE_PREVIOUS_START = "previous_start"
STATE_PREVIOUS_STOP = "previous_stop"

STATUS_DISABLED = "disabled"
STATUS_NO_DEPARTURE = "no_departure"
STATUS_NO_TEMPERATURE = "no_temperature"
STATUS_NO_HEATING_NEEDED = "no_heating_needed"
STATUS_WAITING = "waiting"
STATUS_RUNNING = "running"
STATUS_FINISHED = "finished"
STATUS_START_NOW = "start_now"
