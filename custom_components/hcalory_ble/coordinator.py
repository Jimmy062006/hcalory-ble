from __future__ import annotations

import asyncio
import json
from datetime import timedelta

import aioesphomeapi.core
import hcalory_control.heater
from bleak import BleakError
from bleak_retry_connector import close_stale_connections_by_address
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER

# The Hcalory app scans every 100 milliseconds. That's excessive, but 5 seconds seems reasonable enough.
SCAN_INTERVAL = timedelta(seconds=5)


class HcaloryCoordinator(DataUpdateCoordinator[hcalory_control.heater.HeaterResponse]):
    def __init__(
        self,
        hass: HomeAssistant,
        heater: hcalory_control.heater.HCaloryHeater,
        address: str,
        name: str,
    ) -> None:
        super().__init__(
            hass=hass, logger=LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL
        )
        self.heater: hcalory_control.heater.HCaloryHeater = heater
        self.address: str = address
        self.name: str = name

    async def async_shutdown(self) -> None:
        LOGGER.debug("Shutdown")
        await super().async_shutdown()
        if self.heater.is_connected:
            await self.heater.disconnect()

    async def async_find_device(self):
        LOGGER.debug("Trying to reconnect")
        await close_stale_connections_by_address(self.address)

        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            raise UpdateFailed(
                f"Failed to get async BLE device from address {self.address}"
            )
        if not device.name:
            raise UpdateFailed(
                f"Async BLE device grabbed from {self.address} has no name. An async BLE device needs a name."
            )

        self.heater.device = device

        try:
            await self.heater.get_data()
        except BleakError as e:
            raise UpdateFailed(f"Failed to connect to {self.address}") from e

    async def _async_update_data(self) -> hcalory_control.heater.HeaterResponse:
        LOGGER.debug("Polling device %s", self.address)

        try:
            if not self.heater.is_connected:
                LOGGER.warning(
                    "Heater %s with addr %s is not connected. Trying to reconnect.",
                    self.name,
                    self.address,
                )
                await self.async_find_device()
        except BleakError as err:
            raise UpdateFailed("Failed to connect") from err

        try:
            LOGGER.debug(
                "Fetching data from %s (addr %s) now.", self.name, self.address
            )
            async with asyncio.timeout(30.0):
                data = await self.heater.get_data()
            LOGGER.debug(json.dumps(data.asdict(), indent=4, sort_keys=True))
            return data
        except (
            BleakError,
            ValueError,
            aioesphomeapi.core.BluetoothGATTAPIError,
            TimeoutError,
        ) as err:
            LOGGER.exception(
                "Error getting data from device with addr %s", self.address
            )
            await self.async_find_device()
            raise UpdateFailed(
                f"Error getting data from device with addr {self.address}"
            ) from err
