"""Config flow for Hcalory BLE integration."""

from __future__ import annotations

from typing import Any

import hcalory_control.heater
import voluptuous as vol
from bleak import BleakError
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_ADDRESS,
)

from .const import DEVICE_SERVICE_UUIDS, DOMAIN, LOGGER, MANUFACTURER_BLE_ID


def _is_supported(discovery_info: bluetooth.BluetoothServiceInfo) -> bool:
    LOGGER.debug(
        "(%s) Manufacturer data: %s",
        discovery_info.address,
        discovery_info.manufacturer,
    )
    manufacturer_matches = any(
        key == MANUFACTURER_BLE_ID for key in discovery_info.manufacturer_data
    )
    service_ids_match = DEVICE_SERVICE_UUIDS.issubset(set(discovery_info.service_uuids))

    return manufacturer_matches and service_ids_match


class HcaloryBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self.address: str | None = None
        self._name: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfo
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""

        LOGGER.debug("Discovered device: %s", discovery_info)
        if not _is_supported(discovery_info):
            return self.async_abort(reason="no_devices_found")

        self.address = discovery_info.address
        self._name = discovery_info.name
        await self.async_set_unique_id(self.address)
        self._abort_if_unique_id_configured()
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        LOGGER.debug("(%s) name: %s", self.address, self._name)

        assert self.address
        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            return self.async_abort(reason="no_devices_found")
        if device.name is None:
            return self.async_abort(reason="device_missing_name")
        if self._name is None:
            self._name = device.name

        assert self._name
        try:
            heater = hcalory_control.heater.HCaloryHeater(device)
            await heater.get_data()
        except (BleakError, TimeoutError, ValueError) as e:
            LOGGER.exception("Failed to connect to device: %s", e, exc_info=e)
            return self.async_abort(reason="cannot_connect")

        title = f"{self._name} {self.address}"

        LOGGER.debug("Found device: %s", title)

        if user_input is not None:
            return self.async_create_entry(
                title=title,
                data={CONF_ADDRESS: self.address},
            )

        self.context["title_placeholders"] = {
            "name": title,
        }

        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self.address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(self.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return await self.async_step_confirm()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                },
            ),
        )
