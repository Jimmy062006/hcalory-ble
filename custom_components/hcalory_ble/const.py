"""Constants for the Hcalory BLE integration."""

import logging
from typing import Literal

DataAttributeType = Literal[
    "heater_state",
    "heater_mode",
    "heater_setting",
    "voltage",
    "body_temperature",
    "ambient_temperature",
]
DOMAIN: str = "hcalory_ble"
MANUFACTURER = "HCalory"

GET_DEVICE_TIMEOUT = 5  # seconds
MANUFACTURER_BLE_ID: int = 45548

DEVICE_SERVICE_UUIDS: set[str] = {"0000fff0-0000-1000-8000-00805f9b34fb"}

LOGGER = logging.getLogger(__package__)
