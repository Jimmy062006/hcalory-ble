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
        native_max_value=104.0,
        native_step=1.0,
    )
    async_add_entities([HcalorySettingNumber(coordinator, config, entity_description)])


class HcalorySettingNumber(HcaloryHeaterEntity, NumberEntity):
    def __init__(
        self,
        coordinator: HcaloryCoordinator,
        entry: ConfigEntry[hcalory_control.heater.HCaloryHeater],
        entity_description: NumberEntityDescription,
    ):
        super().__init__(coordinator, entry, entity_description)
        self.change_lock = asyncio.Lock()

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is not None:
            LOGGER.debug(
                "(%s) request for native_value of Setting number yielded %d",
                self.address,
                float(self.coordinator.data.heater_setting),
            )
            return float(self.coordinator.data.heater_setting)
        return None

    async def async_set_native_value(self, value: float) -> None:
        if self.coordinator.data is None:
            LOGGER.warning(
                "(%s) Can't get current value for heater setpoint when beginning change. Giving up.",
                self.address,
            )
            return

        async with self.change_lock:
            original_value = self.coordinator.data.heater_setting
            current_value = original_value
            LOGGER.debug(
                "(%s) Temperature change called. Native value is %d, value from coordinator is is %d, new value is %d",
                self.address,
                self.native_value,
                original_value,
                int(value),
            )
            new_value = int(value)
            while current_value != new_value:
                assumed_state = current_value
                iterator = range(
                    min((current_value, new_value)), max((current_value, new_value))
                )
                LOGGER.debug(
                    "(%s) changing temperature from %d to %d",
                    self.address,
                    current_value,
                    new_value,
                )
                if current_value > new_value:
                    LOGGER.debug("(%s) change is a reduction", self.address)

                    # Mypy is being really dumb because ranges are dumb. If this were a regular
                    # reversible iterable, then reassigning the iterator variable to the reversed
                    # value would be fine. Instead, mypy says this:
                    # error: Incompatible types in assignment (expression has type "reversed[int]", variable has type "range")
                    # That is dumb so I'm doing this:
                    iterator = reversed(iterator)  # type: ignore
                for next_value in iterator:
                    LOGGER.debug(
                        "(%s) Assumed state: %d, next value: %d",
                        self.address,
                        assumed_state,
                        next_value,
                    )
                    if assumed_state < next_value:
                        assumed_state += 1
                        await self.heater.send_command(
                            hcalory_control.heater.Command.up
                        )
                    elif assumed_state > next_value:
                        assumed_state -= 1
                        await self.heater.send_command(
                            hcalory_control.heater.Command.down
                        )
                    await asyncio.sleep(0.1)
                # Going up will be off by one. Gotta love non-inclusive range operations.
                if assumed_state < new_value:
                    assumed_state += 1
                    await self.heater.send_command(hcalory_control.heater.Command.up)
                    LOGGER.debug(
                        "(%s) Assumed state after final increase: %d",
                        self.address,
                        assumed_state,
                    )
                await self.coordinator.async_refresh()
                await asyncio.sleep(10.0)
                if native_value := self.native_value is not None:
                    current_value = int(native_value)
                    LOGGER.debug(
                        "(%s) Current value after everything: %d, original value: %d",
                        self.address,
                        current_value,
                        original_value,
                    )
                    if current_value == original_value:
                        LOGGER.warning(
                            "(%s) Attempt to change set point from %d to %d did not actually change anything. "
                            "Giving up so we don't accidentally change the setpoint to something bonkers.",
                            self.address,
                            original_value,
                            new_value,
                        )
                        return
                else:
                    LOGGER.warning(
                        "(%s) Can't get current value for heater setpoint. Giving up."
                    )
                    return
