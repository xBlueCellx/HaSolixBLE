"""Switch platform."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from SolixBLE import (
    C300,
    C300DC,
    C800,
    C1000,
    C1000G2,
    F2600,
    F3800,
    PortStatus,
    PrimeCharger160w,
    PrimeCharger250w,
    SolixBLEDevice,
)

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import SolixBLEConfigEntry


@dataclass(frozen=True, kw_only=True)
class SolixSwitchDescription:
    """Describe a switch and the device models that provide it."""

    models: tuple[type[SolixBLEDevice], ...]
    name: str
    attribute: str
    state_attribute: str | None
    on_function_attribute: str
    off_function_attribute: str


SWITCH_DESCRIPTIONS = (
    SolixSwitchDescription(
        models=(C300, C800, C1000, C1000G2, F2600, F3800),
        name="AC Output",
        attribute="ac_output",
        state_attribute="ac_output",
        on_function_attribute="turn_ac_on",
        off_function_attribute="turn_ac_off",
    ),
    SolixSwitchDescription(
        models=(C300, C300DC, C1000, C1000G2, F2600, F3800),
        name="DC Output",
        attribute="dc_output",
        state_attribute="dc_output",
        on_function_attribute="turn_dc_on",
        off_function_attribute="turn_dc_off",
    ),
    SolixSwitchDescription(
        models=(C800,),
        name="DC Output",
        attribute="dc_output",
        state_attribute=None,
        on_function_attribute="turn_dc_on",
        off_function_attribute="turn_dc_off",
    ),
    SolixSwitchDescription(
        models=(C300, C800, C1000, F2600),
        name="Display",
        attribute="display_on_off",
        state_attribute=None,
        on_function_attribute="turn_display_on",
        off_function_attribute="turn_display_off",
    ),
    SolixSwitchDescription(
        models=(PrimeCharger160w, PrimeCharger250w),
        name="USB Port C1",
        attribute="usb_port_c1",
        state_attribute="usb_port_c1",
        on_function_attribute="turn_usb_c1_on",
        off_function_attribute="turn_usb_c1_off",
    ),
    SolixSwitchDescription(
        models=(PrimeCharger160w, PrimeCharger250w),
        name="USB Port C2",
        attribute="usb_port_c2",
        state_attribute="usb_port_c2",
        on_function_attribute="turn_usb_c2_on",
        off_function_attribute="turn_usb_c2_off",
    ),
    SolixSwitchDescription(
        models=(PrimeCharger160w, PrimeCharger250w),
        name="USB Port C3",
        attribute="usb_port_c3",
        state_attribute="usb_port_c3",
        on_function_attribute="turn_usb_c3_on",
        off_function_attribute="turn_usb_c3_off",
    ),
    SolixSwitchDescription(
        models=(PrimeCharger250w,),
        name="USB Port C4",
        attribute="usb_port_c4",
        state_attribute="usb_port_c4",
        on_function_attribute="turn_usb_c4_on",
        off_function_attribute="turn_usb_c4_off",
    ),
    SolixSwitchDescription(
        models=(PrimeCharger250w,),
        name="USB Port A1/A2",
        attribute="usb_port_a1_a2",
        state_attribute=None,
        on_function_attribute="turn_usb_a1_a2_on",
        off_function_attribute="turn_usb_a1_a2_off",
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: SolixBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switches supported by the device model."""
    device = config_entry.runtime_data
    async_add_entities(
        SolixSwitchEntity(device, description)
        for description in SWITCH_DESCRIPTIONS
        if type(device) in description.models
    )


class SolixSwitchEntity(SwitchEntity):
    """Representation of a device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        device: SolixBLEDevice,
        description: SolixSwitchDescription,
    ) -> None:
        """Initialize the switch from its description without connecting."""
        self._device = device
        self._address = device.address
        self._state_attribute = description.state_attribute
        self._on_function = getattr(device, description.on_function_attribute)
        self._off_function = getattr(device, description.off_function_attribute)

        self._attr_name = description.name
        self._attr_unique_id = f"{device.address}_{description.attribute}"
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

        if self._state_attribute is not None:
            state = getattr(self._device, self._state_attribute)

            if type(state) is PortStatus:
                if state is PortStatus.UNKNOWN:
                    self._attr_is_on = None
                elif state is PortStatus.NOT_CONNECTED:
                    self._attr_is_on = False
                elif state is PortStatus.OUTPUT:
                    self._attr_is_on = True
                else:
                    message = (
                        f"Unexpected port status '{state}' with type '{type(state)}'!"
                    )
                    raise RuntimeError(message)
            else:
                self._attr_is_on = state

    def _state_change_callback(self) -> None:
        """Run when device informs of state update. Updates local properties."""
        _LOGGER.debug("Received state notification from device %s", self.name)
        self._update_updatable_attributes()
        self.async_write_ha_state()

    async def async_turn_on(self, **_kwargs: object) -> None:
        """Turn the entity on."""
        await self._on_function()

    async def async_turn_off(self, **_kwargs: object) -> None:
        """Turn the entity off."""
        await self._off_function()
