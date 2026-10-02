"""Test sensor for SolixBLE integration."""

import asyncio
from contextlib import ExitStack
from datetime import datetime
from unittest.mock import PropertyMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from SolixBLE import LightStatus, PortStatus

from custom_components.solix_ble.const import DOMAIN

from . import (
    MOCK_C300_DETAILS,
    MOCK_C300_TEST_DATA,
    MOCK_C300DC_DETAILS,
    MOCK_C300DC_TEST_DATA,
    MOCK_C800_DETAILS,
    MOCK_C800_TEST_DATA,
    MOCK_C1000_DETAILS,
    MOCK_C1000_TEST_DATA,
    MOCK_C1000G2_DETAILS,
    MOCK_F2000_DETAILS,
    MOCK_F2000_TEST_DATA,
    MOCK_F2600_DETAILS,
    MOCK_F2600_TEST_DATA,
    MOCK_F3800_DETAILS,
    MOCK_MAGGO_3IN1_DETAILS,
    MOCK_MAGGO_3IN1_TEST_DATA,
    MOCK_PRIME_160_DETAILS,
    MOCK_PRIME_160_TEST_DATA,
    MOCK_PRIME_250_DETAILS,
    MOCK_PRIME_250_TEST_DATA,
    MOCK_PRIME_POWER_BANK_20K_DETAILS,
    MOCK_PRIME_POWER_BANK_20K_TEST_DATA,
    MOCK_SOLAR_BANK_2_DETAILS,
    MOCK_SOLAR_BANK_2_TEST_DATA,
    MOCK_UNKNOWN_DETAILS,
    MOCK_UNKNOWN_TEST_DATA,
    MockDeviceDetails,
    SensorTestData,
)


@pytest.mark.parametrize(
    ("mock_config_entry", "mock_device_details", "class_name", "test_data"),
    [
        pytest.param(
            MOCK_C300_DETAILS,
            MOCK_C300_DETAILS,
            "C300",
            MOCK_C300_TEST_DATA,
            id="c300",
        ),
        pytest.param(
            MOCK_C300DC_DETAILS,
            MOCK_C300DC_DETAILS,
            "C300DC",
            MOCK_C300DC_TEST_DATA,
            id="c300dc",
        ),
        pytest.param(
            MOCK_C800_DETAILS,
            MOCK_C800_DETAILS,
            "C800",
            MOCK_C800_TEST_DATA,
            id="c800",
        ),
        pytest.param(
            MOCK_C1000_DETAILS,
            MOCK_C1000_DETAILS,
            "C1000",
            MOCK_C1000_TEST_DATA,
            id="c1000",
        ),
        pytest.param(
            MOCK_C1000G2_DETAILS,
            MOCK_C1000G2_DETAILS,
            "C1000G2",
            {"temperature": 27},
            id="c1000G2",
        ),
        pytest.param(
            MOCK_F2000_DETAILS,
            MOCK_F2000_DETAILS,
            "F2000",
            MOCK_F2000_TEST_DATA,
            id="f2000",
        ),
        pytest.param(
            MOCK_F2600_DETAILS,
            MOCK_F2600_DETAILS,
            "F2600",
            MOCK_F2600_TEST_DATA,
            id="f2600",
        ),
        pytest.param(
            MOCK_F3800_DETAILS,
            MOCK_F3800_DETAILS,
            "F3800",
            {},
            id="f3800",
        ),
        pytest.param(
            MOCK_PRIME_160_DETAILS,
            MOCK_PRIME_160_DETAILS,
            "PrimeCharger160w",
            MOCK_PRIME_160_TEST_DATA,
            id="prime_160w",
        ),
        pytest.param(
            MOCK_PRIME_250_DETAILS,
            MOCK_PRIME_250_DETAILS,
            "PrimeCharger250w",
            MOCK_PRIME_250_TEST_DATA,
            id="prime_250w",
        ),
        pytest.param(
            MOCK_PRIME_POWER_BANK_20K_DETAILS,
            MOCK_PRIME_POWER_BANK_20K_DETAILS,
            "PrimePowerBank20k",
            MOCK_PRIME_POWER_BANK_20K_TEST_DATA,
            id="prime_power_bank_20k",
        ),
        pytest.param(
            MOCK_MAGGO_3IN1_DETAILS,
            MOCK_MAGGO_3IN1_DETAILS,
            "MagGo3in1",
            MOCK_MAGGO_3IN1_TEST_DATA,
            id="maggo_3in1",
        ),
        pytest.param(
            MOCK_SOLAR_BANK_2_DETAILS,
            MOCK_SOLAR_BANK_2_DETAILS,
            "Solarbank2",
            MOCK_SOLAR_BANK_2_TEST_DATA,
            id="solar_bank_2",
        ),
        pytest.param(
            MOCK_UNKNOWN_DETAILS,
            MOCK_UNKNOWN_DETAILS,
            "Generic",
            MOCK_UNKNOWN_TEST_DATA,
            id="unknown",
        ),
    ],
    indirect=["mock_config_entry"],
)
async def test_sensor_entities(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_details: MockDeviceDetails,
    class_name: str,
    test_data: SensorTestData,
) -> None:
    """Test that the entities are added and show the expected values."""

    mock_config_entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.solix_ble.async_ble_device_from_address",
            return_value=mock_device_details.get_ble_device(),
        ),
        patch(
            "custom_components.solix_ble.async_scanner_count",
            return_value=1,
        ),
        patch(
            f"SolixBLE.{class_name}.connect",
            side_effect=[True],
        ),
        patch(
            f"SolixBLE.{class_name}.connected",
            side_effect=[True],
        ),
        patch(
            f"SolixBLE.{class_name}.negotiated",
            side_effect=[True],
        ),
        patch(
            "SolixBLE.SolixBLEDevice.available",
            side_effect=[True],
        ),
        ExitStack() as dynamic_context,
    ):
        # We dynamically patch all of the sensor entities in the test data
        for key, value in test_data.items():
            dynamic_context.enter_context(
                patch(
                    f"SolixBLE.{class_name}.{key}",
                    new_callable=PropertyMock,
                    return_value=(value[1] if isinstance(value, tuple) else value),
                ),
            )

        # Set up the integration
        assert await async_setup_component(hass, DOMAIN, {}) is True
        await hass.async_block_till_done()
        await asyncio.sleep(1)

        # Check that the entities exist and show the expected values.
        for attribute, expected in test_data.items():
            entity_attribute = attribute
            string_value = None
            if isinstance(expected, tuple):
                entity_attribute, actual_value, *overrides = expected
                string_value = overrides[0] if overrides else None
            else:
                actual_value = expected

            if isinstance(actual_value, datetime):
                value = f"{actual_value.strftime('%Y-%m-%dT%H:%M:%S')}+00:00"
            elif isinstance(actual_value, (PortStatus, LightStatus)):
                value = actual_value.name.capitalize().replace("_", " ")
            elif string_value is not None:
                value = string_value
            else:
                value = str(actual_value)

            entity_id = (
                f"sensor.{mock_config_entry.title.lower().replace(' ', '_')}"
                f"_{entity_attribute}"
            )
            entity = hass.states.get(entity_id)
            assert entity is not None, (
                f"Expected to find '{value}' at '{entity_id}' but instead got None!"
            )
            assert entity.state == value, (
                f"Expected '{value}' at '{entity_id}', but got '{entity.state}'!"
            )
