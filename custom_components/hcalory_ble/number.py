import asyncio

import hcalory_control.heater
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
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
) -> None:
    coordinator: HcaloryCoordinator = hass.data[DOMAIN][config.entry_id]
    entity_description = NumberEntityDescription(
        key="heater_setting",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°F",
        mode=NumberMode.BOX,
        name="Heater Setting",
        native_min_value=1.0,
        native_step=1.0,
    )
    async_add_entities([HcalorySettingNumber(coordinator, config, entity_description)])


class HcalorySettingNumber(HcaloryHeaterEntity, NumberEntity):
    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is not None:
            return float(self.coordinator.data.heater_setting)
        return None

    async def async_set_native_value(self, value: float) -> None:
        if native_value := self.native_value is not None:
            original_value = int(native_value)
            current_value = original_value
        else:
            LOGGER.warning(
                "(%s) Can't get current value for heater setpoint when beginning change. Giving up."
            )
            return
        new_value = int(value)
        while current_value != new_value:
            assumed_state = current_value
            iterator = range(
                min((current_value, new_value)), max((current_value, new_value))
            )
            if current_value > new_value:
                # Mypy is being really dumb because ranges are dumb. If this were a regular
                # reversible iterable, then reassigning the iterator variable to the reversed
                # value would be fine. Instead, mypy says this:
                # error: Incompatible types in assignment (expression has type "reversed[int]", variable has type "range")
                # That is dumb so I'm doing this:
                iterator = reversed(iterator)  # type: ignore
            for next_value in iterator:
                if assumed_state < next_value:
                    assumed_state += 1
                    await self.heater.send_command(hcalory_control.heater.Command.up)
                elif assumed_state > next_value:
                    assumed_state -= 1
                    await self.heater.send_command(hcalory_control.heater.Command.down)
                await asyncio.sleep(0.1)
            # Going up will be off by one. Gotta love non-inclusive range operations.
            if assumed_state < new_value:
                assumed_state += 1
                await self.heater.send_command(hcalory_control.heater.Command.up)
            await asyncio.sleep(1.0)
            await self.coordinator.async_refresh()
            if native_value := self.native_value is not None:
                current_value = int(native_value)
                if current_value == original_value:
                    LOGGER.warning(
                        "(%s) Attempt to change set point from %d to %d did not actually change anything. "
                        "Giving up so we don't accidentally change the setpoint to something bonkers.",
                        self.address,
                        original_value,
                        new_value,
                    )
            else:
                LOGGER.warning(
                    "(%s) Can't get current value for heater setpoint. Giving up."
                )
                break
