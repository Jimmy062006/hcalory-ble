import enum
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Generic, TypeVar

import hcalory_control.heater
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, DataAttributeType
from .coordinator import HcaloryCoordinator
from .entity import HcaloryHeaterEntity

_T = TypeVar("_T")


@dataclass(frozen=True, kw_only=True)
class HcalorySensorDescription(SensorEntityDescription, Generic[_T]):
    data_attribute: DataAttributeType


SENSORS: tuple[HcalorySensorDescription, ...] = (
    HcalorySensorDescription[str](
        key="heater_state",
        device_class=SensorDeviceClass.ENUM,
        options=hcalory_control.heater.HeaterState.list(),
        data_attribute="heater_state",
        name="Heater State",
    ),
    HcalorySensorDescription[int](
        key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="V",
        data_attribute="voltage",
        name="Voltage",
    ),
    HcalorySensorDescription[int](
        key="body_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°F",
        data_attribute="body_temperature",
        name="Body Temperature",
    ),
    HcalorySensorDescription[int](
        key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°F",
        data_attribute="ambient_temperature",
        name="Ambient Temperature",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry[hcalory_control.heater.HCaloryHeater],
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HcaloryCoordinator = hass.data[DOMAIN][config.entry_id]
    entities = [
        HcalorySensor[HcalorySensorDescription](coordinator, config, entity_description)
        for entity_description in SENSORS
    ]

    async_add_entities(entities)


class HcalorySensor(
    HcaloryHeaterEntity,
    SensorEntity,
    Generic[_T],
):
    SensorEntityDescription: HcalorySensorDescription[_T]
    # Mypy doesn't seem to understand that an HcalorySensorDescription is a subclass of the EntityDescription
    # that the typevar is bound to over in entity.py. Alternatively (and much more likely), I suck at
    # devlop and do not understand how to type system.
    entity_description: HcalorySensorDescription[_T]

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        if self.coordinator.data is not None:
            data = getattr(
                self.coordinator.data, self.entity_description.data_attribute
            )
            if isinstance(data, enum.Enum):
                return data.name
            return data
