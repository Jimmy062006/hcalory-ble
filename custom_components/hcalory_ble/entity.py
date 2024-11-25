from typing import Generic, TypeVar

import hcalory_control.heater
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.typing import UndefinedType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import MANUFACTURER
from .coordinator import HcaloryCoordinator

_T = TypeVar("_T", bound=EntityDescription)


class HcaloryHeaterEntity(CoordinatorEntity[HcaloryCoordinator], Generic[_T]):
    def __init__(
        self,
        coordinator: HcaloryCoordinator,
        entry: ConfigEntry[hcalory_control.heater.HCaloryHeater],
        entity_description: _T,
    ):
        super().__init__(coordinator)
        self.entry = entry
        self.entity_description = entity_description
        self.heater = self.entry.runtime_data
        self.address = self.entry.data[CONF_ADDRESS]
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, self.address)},
            manufacturer=MANUFACTURER,
            name=coordinator.name,
        )

    @property
    def name(self) -> str | UndefinedType | None:
        return f"{self.coordinator.name} {self.entity_description.key.replace("_", " ").title()}"

    @property
    def unique_id(self) -> str | None:
        return slugify(f"{self.coordinator.name}_{self.entity_description.key}")
