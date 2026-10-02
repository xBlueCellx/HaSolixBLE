"""SolixBLE integration."""

import logging

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_scanner_count,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from SolixBLE import (
    C300,
    C300DC,
    C800,
    C1000,
    C1000G2,
    F2000,
    F2600,
    F3800,
    Generic,
    MagGo3in1,
    PrimeCharger160w,
    PrimeCharger250w,
    PrimePowerBank20k,
    Solarbank2,
    SolixBLEDevice,
)

from .const import Models

_LOGGER = logging.getLogger(__name__)

type SolixBLEConfigEntry = ConfigEntry[SolixBLEDevice]


DEVICE_CLASSES: dict[Models, type[SolixBLEDevice]] = {
    Models.C300: C300,
    Models.C300DC: C300DC,
    Models.C800: C800,
    Models.C1000: C1000,
    Models.C1000G2: C1000G2,
    Models.F2000: F2000,
    Models.F2600: F2600,
    Models.F3800: F3800,
    Models.PRIME_CHARGER_160: PrimeCharger160w,
    Models.PRIME_CHARGER_250: PrimeCharger250w,
    Models.PRIME_POWER_BANK_20K: PrimePowerBank20k,
    Models.MAGGO_3IN1: MagGo3in1,
    Models.SOLARBANK_2: Solarbank2,
    Models.UNKNOWN: Generic,
}


def get_power_station_class(model: Models) -> type[SolixBLEDevice]:
    """Return the device class for a power station model."""
    try:
        return DEVICE_CLASSES[model]
    except KeyError as error:
        message = f"Unexpected model. Got: '{type(model)}'!"
        raise NotImplementedError(message) from error


async def async_setup_entry(hass: HomeAssistant, entry: SolixBLEConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    if entry.unique_id is None:
        message = "The config entry has no Bluetooth address."
        raise ConfigEntryNotReady(message)
    address = entry.unique_id.upper()
    model = Models(entry.data["model"])

    ble_device = async_ble_device_from_address(hass, address, connectable=True)

    if ble_device is None:
        count_scanners = async_scanner_count(hass, connectable=True)
        _LOGGER.debug("Count of BLE scanners: %i", count_scanners)

        if count_scanners < 1:
            message = "No Bluetooth scanners are available to search for the device."
            raise ConfigEntryNotReady(message)
        message = "The device was not found."
        raise ConfigEntryNotReady(message)

    device_class = get_power_station_class(model)
    if model is Models.UNKNOWN:
        _LOGGER.warning(
            "The device '%s' is not supported and values will not be available "
            "to Home Assistant! However when the integration is in debug mode "
            "the raw telemetry data and differences between status updates will "
            "be printed in the log and this can be used to aid in adding support "
            "for new devices.",
            ble_device.name,
        )

    device = device_class(ble_device)
    try:
        await device.connect()
    except Exception as e:
        message = "Unexpected exception when connecting to device."
        raise ConfigEntryNotReady(message) from e

    if not device.connected:
        message = "Device found but unable to connect."
        raise ConfigEntryNotReady(message)

    if not device.negotiated:
        message = "Device connected but failed to negotiate encryption."
        raise ConfigEntryNotReady(message)

    entry.runtime_data = device

    await hass.config_entries.async_forward_entry_setups(
        entry,
        [Platform.SENSOR, Platform.SWITCH],
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SolixBLEConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok_sensor = await hass.config_entries.async_forward_entry_unload(
        entry,
        Platform.SENSOR,
    )
    unload_ok_switch = await hass.config_entries.async_forward_entry_unload(
        entry,
        Platform.SWITCH,
    )

    await entry.runtime_data.disconnect()

    del entry.runtime_data

    return unload_ok_sensor and unload_ok_switch
