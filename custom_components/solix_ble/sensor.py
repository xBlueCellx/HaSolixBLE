"""sensor platform."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.util.dt import as_local
from SolixBLE import (
    C300,
    C300DC,
    C800,
    C1000,
    C1000G2,
    F2000,
    F2600,
    F3800,
    MagGo3in1,
    PrimeCharger160w,
    PrimeCharger250w,
    PrimePowerBank20k,
    Solarbank2,
    SolixBLEDevice,
)

from .const import (
    CHARGING_STATUS_C300_STRINGS,
    CHARGING_STATUS_F3800_STRINGS,
    CUT_OFF_SB2_STRINGS,
    GRID_STATUS_STRINGS,
    LIGHT_STATUS_SB2_STRINGS,
    LIGHT_STATUS_STRINGS,
    MAX_LOAD_SB2_STRINGS,
    OVERLOAD_STATUS_C300DC_STRINGS,
    PORT_STATUS_STRINGS,
    USAGE_MODE_SB2_STRINGS,
)

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import SolixBLEConfigEntry


@dataclass(frozen=True, kw_only=True)
class SolixSensorDescription:
    """Describe a sensor and the device models that provide it."""

    models: tuple[type[SolixBLEDevice], ...]
    name: str
    unit: str | None
    attribute: str
    device_class: SensorDeviceClass | None = None
    enum_options: list[str] | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT


SENSOR_DESCRIPTIONS = (
    SolixSensorDescription(
        models=(C300, C300DC),
        name="Charging Status",
        unit=None,
        attribute="charging_status",
        device_class=SensorDeviceClass.ENUM,
        enum_options=CHARGING_STATUS_C300_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(F2600, F3800),
        name="Charging Status",
        unit=None,
        attribute="charging_status",
        device_class=SensorDeviceClass.ENUM,
        enum_options=CHARGING_STATUS_F3800_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, F2000, F2600, F3800),
        name="Remaining Hours",
        unit="hours",
        attribute="hours_remaining",
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, F2000, F2600, F3800),
        name="Remaining Days",
        unit="days",
        attribute="days_remaining",
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, F2000, F2600, F3800),
        name="Remaining Time",
        unit="hours",
        attribute="time_remaining",
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, F2000, F2600, F3800),
        name="Timestamp Remaining",
        unit=None,
        attribute="timestamp_remaining",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C800,
            C1000,
            C1000G2,
            F2000,
            F2600,
            F3800,
            Solarbank2,
            PrimePowerBank20k,
        ),
        name="Battery Percentage",
        unit="%",
        attribute="battery_percentage",
        device_class=SensorDeviceClass.BATTERY,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Battery charge power",
        unit="W",
        attribute="battery_charge_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Battery discharge power",
        unit="W",
        attribute="battery_discharge_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(C300DC, C800, C1000, C1000G2, F2000, F2600),
        name="Battery Health",
        unit="%",
        attribute="battery_health",
        device_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Battery input energy",
        unit="kWh",
        attribute="charged_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Total output energy",
        unit="kWh",
        attribute="output_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Output cutoff threshold",
        unit=None,
        attribute="output_cutoff_data",
        device_class=SensorDeviceClass.ENUM,
        enum_options=CUT_OFF_SB2_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Input cutoff threshold",
        unit=None,
        attribute="input_cutoff_data",
        device_class=SensorDeviceClass.ENUM,
        enum_options=CUT_OFF_SB2_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C800,
            C1000,
            C1000G2,
            F2000,
            F2600,
            F3800,
            Solarbank2,
            PrimePowerBank20k,
        ),
        name="Temperature",
        unit=UnitOfTemperature.CELSIUS,
        attribute="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, F2600),
        name="Total Power In",
        unit="W",
        attribute="power_in",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C800,
            C1000,
            C1000G2,
            F2600,
            F3800,
            Solarbank2,
            PrimePowerBank20k,
            MagGo3in1,
        ),
        name="Total Power Out",
        unit="W",
        attribute="power_out",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(C300, C800, C1000, C1000G2, F2000, F2600, F3800),
        name="AC Power In",
        unit="W",
        attribute="ac_power_in",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(C300, C800, C1000, C1000G2, F2000, F2600, F3800, Solarbank2),
        name="AC Power Out",
        unit="W",
        attribute="ac_power_out",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(C300, C800, C1000, C1000G2, F2600, F3800),
        name="Status AC Out",
        unit=None,
        attribute="ac_output",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C800, C1000, F2600),
        name="AC Timer",
        unit=None,
        attribute="ac_timer",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, C1000G2, F2000, F2600, F3800, Solarbank2),
        name="Solar Power In",
        unit="W",
        attribute="solar_power_in",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="PV Yield",
        unit="kWh",
        attribute="pv_yield",
        device_class=SensorDeviceClass.ENERGY,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C1000, C1000G2),
        name="DC Power Out",
        unit="W",
        attribute="dc_power_out",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(F2600,),
        name="DC Power Out 1",
        unit="W",
        attribute="dc_1_power_out",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(F2600,),
        name="DC Power Out 2",
        unit="W",
        attribute="dc_2_power_out",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(C300DC, F2600),
        name="Status Solar",
        unit=None,
        attribute="solar_port",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C1000, C1000G2, F3800),
        name="Status DC Out",
        unit=None,
        attribute="dc_output",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, F2600),
        name="DC Timer",
        unit=None,
        attribute="dc_timer",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C800,
            C1000,
            C1000G2,
            F2000,
            F2600,
            F3800,
            PrimeCharger160w,
            PrimeCharger250w,
            PrimePowerBank20k,
        ),
        name="USB C1 Power",
        unit="W",
        attribute="usb_c1_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C800,
            C1000,
            C1000G2,
            F2000,
            F2600,
            F3800,
            PrimeCharger160w,
            PrimeCharger250w,
            PrimePowerBank20k,
        ),
        name="USB C2 Power",
        unit="W",
        attribute="usb_c2_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C1000G2,
            F2000,
            F2600,
            F3800,
            PrimeCharger160w,
            PrimeCharger250w,
        ),
        name="USB C3 Power",
        unit="W",
        attribute="usb_c3_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(C300DC, PrimeCharger250w),
        name="USB C4 Power",
        unit="W",
        attribute="usb_c4_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C800,
            C1000,
            C1000G2,
            F2000,
            F2600,
            F3800,
            PrimeCharger250w,
            PrimePowerBank20k,
        ),
        name="USB A1 Power",
        unit="W",
        attribute="usb_a1_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(C300DC, C800, C1000, F2000, F2600, F3800, PrimeCharger250w),
        name="USB A2 Power",
        unit="W",
        attribute="usb_a2_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C1000G2,
            F2600,
            F3800,
            PrimeCharger160w,
            PrimeCharger250w,
            PrimePowerBank20k,
        ),
        name="Status USB C1",
        unit=None,
        attribute="usb_port_c1",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C1000G2,
            F2600,
            F3800,
            PrimeCharger160w,
            PrimeCharger250w,
            PrimePowerBank20k,
        ),
        name="Status USB C2",
        unit=None,
        attribute="usb_port_c2",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C1000G2,
            F2600,
            F3800,
            PrimeCharger160w,
            PrimeCharger250w,
        ),
        name="Status USB C3",
        unit=None,
        attribute="usb_port_c3",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300DC, PrimeCharger250w),
        name="Status USB C4",
        unit=None,
        attribute="usb_port_c4",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(
            C300,
            C300DC,
            C1000G2,
            F2600,
            F3800,
            PrimeCharger250w,
            PrimePowerBank20k,
        ),
        name="Status USB A1",
        unit=None,
        attribute="usb_port_a1",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300DC, F2600, F3800, PrimeCharger250w),
        name="Status USB A2",
        unit=None,
        attribute="usb_port_a2",
        device_class=SensorDeviceClass.ENUM,
        enum_options=PORT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300DC,),
        name="Overload Status",
        unit=None,
        attribute="device_overload",
        device_class=SensorDeviceClass.ENUM,
        enum_options=OVERLOAD_STATUS_C300DC_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(PrimeCharger160w, PrimeCharger250w, PrimePowerBank20k),
        name="USB C1 Voltage",
        unit="V",
        attribute="usb_c1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SolixSensorDescription(
        models=(PrimeCharger160w, PrimeCharger250w, PrimePowerBank20k),
        name="USB C2 Voltage",
        unit="V",
        attribute="usb_c2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SolixSensorDescription(
        models=(PrimeCharger160w, PrimeCharger250w),
        name="USB C3 Voltage",
        unit="V",
        attribute="usb_c3_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SolixSensorDescription(
        models=(PrimeCharger250w,),
        name="USB C4 Voltage",
        unit="V",
        attribute="usb_c4_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SolixSensorDescription(
        models=(PrimeCharger250w, PrimePowerBank20k),
        name="USB A1 Voltage",
        unit="V",
        attribute="usb_a1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SolixSensorDescription(
        models=(PrimeCharger250w,),
        name="USB A2 Voltage",
        unit="V",
        attribute="usb_a2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SolixSensorDescription(
        models=(PrimeCharger160w, PrimeCharger250w, PrimePowerBank20k),
        name="USB C1 Current",
        unit="A",
        attribute="usb_c1_current",
        device_class=SensorDeviceClass.CURRENT,
    ),
    SolixSensorDescription(
        models=(PrimeCharger160w, PrimeCharger250w, PrimePowerBank20k),
        name="USB C2 Current",
        unit="A",
        attribute="usb_c2_current",
        device_class=SensorDeviceClass.CURRENT,
    ),
    SolixSensorDescription(
        models=(PrimeCharger160w, PrimeCharger250w),
        name="USB C3 Current",
        unit="A",
        attribute="usb_c3_current",
        device_class=SensorDeviceClass.CURRENT,
    ),
    SolixSensorDescription(
        models=(PrimeCharger250w,),
        name="USB C4 Current",
        unit="A",
        attribute="usb_c4_current",
        device_class=SensorDeviceClass.CURRENT,
    ),
    SolixSensorDescription(
        models=(PrimeCharger250w, PrimePowerBank20k),
        name="USB A1 Current",
        unit="A",
        attribute="usb_a1_current",
        device_class=SensorDeviceClass.CURRENT,
    ),
    SolixSensorDescription(
        models=(PrimeCharger250w,),
        name="USB A2 Current",
        unit="A",
        attribute="usb_a2_current",
        device_class=SensorDeviceClass.CURRENT,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, F2600),
        name="Status Light",
        unit=None,
        attribute="light",
        device_class=SensorDeviceClass.ENUM,
        enum_options=LIGHT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300DC, F2600),
        name="Display Status",
        unit=None,
        attribute="display_mode",
        device_class=SensorDeviceClass.ENUM,
        enum_options=LIGHT_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Error code",
        unit=None,
        attribute="error_code",
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, F2000, F2600, F3800, Solarbank2),
        name="Firmware Version",
        unit=None,
        attribute="software_version",
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C300, C300DC, C800, C1000, C1000G2, F2000, F2600, F3800, Solarbank2),
        name="Serial Number",
        unit=None,
        attribute="serial_number",
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C1000, F2000, F2600),
        name="Expansion Battery Temperature",
        unit=UnitOfTemperature.CELSIUS,
        attribute="temperature_expansion",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SolixSensorDescription(
        models=(C1000, F2000, F2600),
        name="Expansion Battery Percentage",
        unit="%",
        attribute="battery_percentage_expansion",
        device_class=SensorDeviceClass.BATTERY,
    ),
    SolixSensorDescription(
        models=(F3800, Solarbank2),
        name="Average Battery Percentage",
        unit="%",
        attribute="battery_percentage_aggregate",
        device_class=SensorDeviceClass.BATTERY,
    ),
    SolixSensorDescription(
        models=(C1000, F2000, F2600),
        name="Expansion Battery Health",
        unit="%",
        attribute="battery_health_expansion",
        device_class=SensorDeviceClass.BATTERY,
    ),
    SolixSensorDescription(
        models=(C1000, F2000, F2600, Solarbank2),
        name="Expansion Battery Firmware Version",
        unit=None,
        attribute="software_version_expansion",
        state_class=None,
    ),
    SolixSensorDescription(
        models=(C1000, F2000, F2600),
        name="Number Of Expansion Batteries",
        unit=None,
        attribute="num_expansion",
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Grid to Home power",
        unit="W",
        attribute="grid_to_home_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="PV to Grid power",
        unit="W",
        attribute="pv_to_grid_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Grid import energy",
        unit="kWh",
        attribute="grid_import_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Grid export energy",
        unit="kWh",
        attribute="grid_export_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="House demand power",
        unit="W",
        attribute="house_demand",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="House consumed energy",
        unit="kWh",
        attribute="consumed_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(F2600, Solarbank2),
        name="AC Power Out Sockets",
        unit="W",
        attribute="ac_power_out_sockets",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Maximum load",
        unit=None,
        attribute="max_load",
        device_class=SensorDeviceClass.ENUM,
        enum_options=MAX_LOAD_SB2_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Usage mode",
        unit=None,
        attribute="usage_mode",
        device_class=SensorDeviceClass.ENUM,
        enum_options=USAGE_MODE_SB2_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Solar Power In Port 1",
        unit="W",
        attribute="solar_pv_1_power_in",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Solar Power In Port 2",
        unit="W",
        attribute="solar_pv_2_power_in",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Solar Power In Port 3",
        unit="W",
        attribute="solar_pv_3_power_in",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Solar Power In Port 4",
        unit="W",
        attribute="solar_pv_4_power_in",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Status light",
        unit=None,
        attribute="light_mode",
        device_class=SensorDeviceClass.ENUM,
        enum_options=LIGHT_STATUS_SB2_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Grid Status",
        unit=None,
        attribute="grid_status",
        device_class=SensorDeviceClass.ENUM,
        enum_options=GRID_STATUS_STRINGS,
        state_class=None,
    ),
    SolixSensorDescription(
        models=(Solarbank2,),
        name="Battery Heating",
        unit=None,
        attribute="battery_heating",
        device_class=None,
    ),
    SolixSensorDescription(
        models=(MagGo3in1,),
        name="Pad 1 Power",
        unit="W",
        attribute="pad_1_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(MagGo3in1,),
        name="Pad 2 Power",
        unit="W",
        attribute="pad_2_power",
        device_class=SensorDeviceClass.POWER,
    ),
    SolixSensorDescription(
        models=(MagGo3in1,),
        name="Pad 3 Power",
        unit="W",
        attribute="pad_3_power",
        device_class=SensorDeviceClass.POWER,
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors supported by the device model."""
    device = config_entry.runtime_data
    async_add_entities(
        SolixSensorEntity(device, description)
        for description in SENSOR_DESCRIPTIONS
        if type(device) in description.models
    )


class SolixSensorEntity(SensorEntity):
    """Representation of a device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        device: SolixBLEDevice,
        description: SolixSensorDescription,
    ) -> None:
        """Initialize the device object. Does not connect."""

        self._attribute_name = description.attribute

        self._device = device
        self._address = device.address
        self._attr_name = description.name
        self._attr_unique_id = f"{device.address}_{description.attribute}"
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_options = description.enum_options
        self._attr_state_class = description.state_class
        self._attr_device_info = DeviceInfo(
            name=device.name,
            connections={(CONNECTION_BLUETOOTH, device.address)},
        )
        self._update_updatable_attributes()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._device.add_callback(self._state_change_callback)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from HA."""
        self._device.remove_callback(self._state_change_callback)

    def _update_updatable_attributes(self) -> None:
        """Update this entities updatable attrs from the devices state."""
        self._attr_available = self._device.available

        attribute_value = getattr(self._device, self._attribute_name)

        # If none pass through
        if attribute_value is None:
            self._attr_native_value = attribute_value

        # If timestamp add timezone info
        elif self._attr_device_class is SensorDeviceClass.TIMESTAMP:
            self._attr_native_value = as_local(attribute_value)

        # If enum use enum strings
        elif self._attr_device_class == SensorDeviceClass.ENUM:
            if self._attr_options is None or not isinstance(attribute_value, Enum):
                message = "Enum sensors require options and an enum value"
                raise ValueError(message)
            self._attr_native_value = self._attr_options[
                list(type(attribute_value)).index(attribute_value)
            ]

        # Else pass through value
        else:
            self._attr_native_value = attribute_value

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()
