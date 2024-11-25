import asyncio
from typing import Any

import bleak
import hcalory_control.heater
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import HcaloryCoordinator
from .entity import HcaloryHeaterEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry[hcalory_control.heater.HCaloryHeater],
    async_add_entities: AddEntitiesCallback,
) -> bool:
    coordinator: HcaloryCoordinator = hass.data[DOMAIN][config.entry_id]
    entity_description = SwitchEntityDescription(
        key="heater_power", device_class=SwitchDeviceClass.SWITCH, name="Heater Power"
    )
    async_add_entities([HcalorySwitch(coordinator, config, entity_description)])
    return True


class HcalorySwitch(HcaloryHeaterEntity, SwitchEntity):
    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is not None:
            LOGGER.debug(
                "(%s) running: %s",
                self.address,
                self.coordinator.data.running,
            )
            return self.coordinator.data.running
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        LOGGER.debug(
            "(%s) turning on. Is connected: %s",
            self.address,
            self.heater.is_connected,
        )
        try:
            await self.coordinator.async_find_device()
            await self.heater.get_data()
            await self.heater.send_command(hcalory_control.heater.Command.start_heat)
            await asyncio.sleep(1.0)
            await self.heater.get_data()
        except (TimeoutError, bleak.BleakError, AttributeError) as e:
            await self.coordinator.async_find_device()
            LOGGER.exception(
                "Encountered exception: %s while turning on switch %s",
                e,
                self.address,
            )
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        LOGGER.debug(
            "(%s) turning off. Is connected: %s",
            self.address,
            self.heater.is_connected,
        )
        try:
            await self.heater.get_data()
            await self.heater.send_command(hcalory_control.heater.Command.stop_heat)
            await asyncio.sleep(1.0)
            await self.heater.get_data()
        except (TimeoutError, bleak.BleakError, AttributeError) as e:
            await self.coordinator.async_find_device()
            LOGGER.exception(
                "Encountered exception: %s while turning off switch %s",
                e,
                self.address,
            )
            raise
