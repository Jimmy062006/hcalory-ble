"""The Hcalory BLE integration."""

from __future__ import annotations

import bleak
import bleak_retry_connector
import hcalory_control.heater
import homeassistant.components.bluetooth
import homeassistant.exceptions
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER
from .coordinator import HcaloryCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.NUMBER,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[hcalory_control.heater.HCaloryHeater]
) -> bool:
    mac_address = entry.data[CONF_ADDRESS]
    LOGGER.debug("(%s) Setting up device", mac_address)
    mac_address = entry.data[CONF_ADDRESS]
    LOGGER.debug("(%s) Closing any stale connections", mac_address)
    await bleak_retry_connector.close_stale_connections_by_address(mac_address)
    LOGGER.debug("(%s) Attempting to connect", mac_address)
    try:
        ble_device = async_ble_device_from_address(hass, mac_address, connectable=True)
        if ble_device is None:
            LOGGER.debug(
                "(%s) async_ble_device_from_address failed, using bleak_retry_connector",
                mac_address,
            )
            ble_device = await bleak_retry_connector.get_device(mac_address)
            if ble_device is None:
                raise homeassistant.exceptions.ConfigEntryNotReady(
                    f"{mac_address} Could not get BLEDevice. We cannot get a name this way. A heater needs a name."
                )

        if not ble_device.name:
            raise homeassistant.exceptions.ConfigEntryNotReady(
                f"Device with address {mac_address} didn't give us a name. A heater needs a name."
            )
        device = hcalory_control.heater.HCaloryHeater(ble_device)
        await device.get_data()
    except (TimeoutError, bleak.BleakError) as e:
        raise homeassistant.exceptions.ConfigEntryNotReady(
            f"Unable to connect to device {mac_address}"
        ) from e
    LOGGER.debug("(%s) Connected and paired", mac_address)
    entry.runtime_data = device
    device_name = ble_device.name
    if device_name is None:
        raise homeassistant.exceptions.ConfigEntryNotReady(
            f"Device with address {mac_address} unaccountably _still_ didn't give us a name. A. Device. Needs. A. Name."
        )
    _coordinator = HcaloryCoordinator(hass, device, mac_address, device_name)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry[hcalory_control.heater.HCaloryHeater]
) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        heater: hcalory_control.heater.HCaloryHeater = entry.runtime_data
        await heater.disconnect()

    return unload_ok
