"""Common fixtures for the Solix BLE tests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solix_ble.const import DOMAIN

from . import MockDeviceDetails

if TYPE_CHECKING:
    from collections.abc import Generator

    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_bluetooth_dependency(hass: HomeAssistant) -> Generator[None]:
    """Auto-mock bluetooth and bluetooth_adapters dependencies."""
    # This mock prevents 'bluetooth_adapters' from failing during setup
    with (
        patch(
            "homeassistant.components.bluetooth_adapters.async_setup",
            return_value=True,
        ),
        patch("homeassistant.components.bluetooth.async_setup", return_value=True),
    ):
        hass.config.components.add("bluetooth")
        hass.config.components.add("bluetooth_adapters")
        yield


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in every test."""


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.solix_ble.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry(request: pytest.FixtureRequest) -> MockConfigEntry:
    """Create a mock config entry."""
    _LOGGER.debug(f"Creating mock config entry using: {request.param}")
    assert isinstance(request.param, MockDeviceDetails)
    return MockConfigEntry(
        domain=DOMAIN,
        title=request.param.name,
        unique_id=request.param.addr.lower(),
        data={"model": request.param.model_class.value},
    )
