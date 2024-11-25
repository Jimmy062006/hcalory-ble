import asyncio

import hcalory_control.heater
from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
    entity_description = SelectEntityDescription(
        key="heater_mode",
        name="Heater Mode",
        options=["gear", "thermostat"],
    )
    async_add_entities(
        [HcaloryModeSelectEntity(coordinator, config, entity_description)]
    )
    return True


class HcaloryModeSelectEntity(HcaloryHeaterEntity, SelectEntity):
    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is not None:
            current_mode = hcalory_control.heater.HeaterMode[
                self.coordinator.data.heater_mode.name
            ]
            if (
                current_mode == hcalory_control.heater.HeaterMode.off
                or current_mode == hcalory_control.heater.HeaterMode.ignition_failed
            ):
                return None
            return self.coordinator.data.heater_mode.name

    async def async_select_option(self, option: str) -> None:
        LOGGER.debug("(%s) selecting option %s", self.address, option)
        assert option in self.options
        await self.heater.send_command(hcalory_control.heater.Command[option])
        await asyncio.sleep(
            1
        )  # TODO yuck, I wish this heater wasn't so grody. Find a way to get rid of this please
        await self.coordinator.async_refresh()
