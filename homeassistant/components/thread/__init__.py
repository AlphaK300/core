"""The Thread integration."""
from __future__ import annotations

from http import HTTPStatus

import aiohttp
import voluptuous as vol

from homeassistant.components.hassio import AddonError, AddonInfo, AddonManager
from homeassistant.components.homeassistant_hardware.silabs_multiprotocol_addon import (
    get_addon_manager,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .models import OperationalDataSet, ThreadState

DOMAIN = "thread"

DATA_ADDON_MANAGER = "silabs_multiprotocol_addon_manager"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Thread."""

    return True


REST_API_PORT = 8081


async def _async_get_thread_rest_service_url(hass) -> str:
    """Return Thread REST API URL."""
    addon_manager: AddonManager = get_addon_manager(hass)
    try:
        addon_info: AddonInfo = await addon_manager.async_get_addon_info()
    except AddonError as err:
        raise HomeAssistantError from err

    if not addon_info.hostname:
        raise HomeAssistantError

    return f"http://{addon_info.hostname}:{REST_API_PORT}"


async def async_get_thread_state(hass: HomeAssistant) -> ThreadState:
    """Get current Thread state."""

    response = await async_get_clientsession(hass).get(
        f"{await _async_get_thread_rest_service_url(hass)}/node/state",
        timeout=aiohttp.ClientTimeout(total=10),
    )

    response.raise_for_status()
    if response.status != HTTPStatus.OK:
        raise HomeAssistantError

    try:
        state = ThreadState(int(await response.read()))
    except (TypeError, ValueError) as exc:
        raise HomeAssistantError from exc

    return state


async def async_set_thread_state(hass: HomeAssistant, state: ThreadState) -> None:
    """Set current Thread state."""

    response = await async_get_clientsession(hass).post(
        f"{await _async_get_thread_rest_service_url(hass)}/node/state",
        data=str(state.value),
        timeout=aiohttp.ClientTimeout(total=10),
    )

    response.raise_for_status()
    if response.status != HTTPStatus.OK:
        raise HomeAssistantError


async def async_get_active_dataset(hass: HomeAssistant) -> OperationalDataSet:
    """Get current active operational dataset.

    Raises if the http status is 400 or higher or if the response is invalid.
    """

    response = await async_get_clientsession(hass).get(
        f"{await _async_get_thread_rest_service_url(hass)}/node/dataset/active",
        timeout=aiohttp.ClientTimeout(total=10),
    )

    response.raise_for_status()
    if response.status != HTTPStatus.OK:
        raise HomeAssistantError

    try:
        return OperationalDataSet.from_json(await response.json())
    except vol.Error as exc:
        raise HomeAssistantError from exc


async def async_get_active_dataset_tlvs(hass: HomeAssistant) -> bytes:
    """Get current active operational dataset in TLVS format.

    Raises if the http status is 400 or higher or if the response is invalid.
    """

    response = await async_get_clientsession(hass).get(
        f"{await _async_get_thread_rest_service_url(hass)}/node/dataset/active",
        headers={"Accept": "text/plain"},
        timeout=aiohttp.ClientTimeout(total=10),
    )

    response.raise_for_status()
    if response.status != HTTPStatus.OK:
        raise HomeAssistantError

    try:
        tmp = await response.read()
        return bytes.fromhex(tmp.decode("ASCII"))
    except vol.Error as exc:
        raise HomeAssistantError from exc


async def async_create_active_dataset(
    hass: HomeAssistant, dataset: OperationalDataSet
) -> None:
    """Create active operational dataset.

    The passed in OperationalDataSet does not need to be fully populated, any fields
    not set will be automatically set by the open thread border router.
    Raises if the http status is 400 or higher or if the response is invalid.
    """

    response = await async_get_clientsession(hass).post(
        f"{await _async_get_thread_rest_service_url(hass)}/node/dataset/active",
        json=dataset.as_json(),
        timeout=aiohttp.ClientTimeout(total=10),
    )

    response.raise_for_status()
    if response.status != HTTPStatus.OK:
        raise HomeAssistantError


async def async_set_active_dataset(
    hass: HomeAssistant, dataset: OperationalDataSet
) -> None:
    """Set current active operational dataset.

    The passed in OperationalDataSet does not need to be fully populated, any fields
    not set will be automatically copied from the current active dataset.
    Raises if the http status is 400 or higher or if the response is invalid.
    """

    response = await async_get_clientsession(hass).put(
        f"{await _async_get_thread_rest_service_url(hass)}/node/dataset/active",
        json=dataset.as_json(),
        timeout=aiohttp.ClientTimeout(total=10),
    )

    response.raise_for_status()
    if response.status != HTTPStatus.OK:
        raise HomeAssistantError


async def async_set_active_dataset_tlvs(hass: HomeAssistant, dataset: bytes) -> None:
    """Set current active operational dataset.

    The passed in OperationalDataSet does not need to be fully populated, any fields
    not set will be automatically copied from the current active dataset.
    Raises if the http status is 400 or higher or if the response is invalid.
    """

    response = await async_get_clientsession(hass).put(
        f"{await _async_get_thread_rest_service_url(hass)}/node/dataset/active",
        data=dataset.hex(),
        headers={"Content-Type": "text/plain"},
        timeout=aiohttp.ClientTimeout(total=10),
    )

    response.raise_for_status()
    if response.status != HTTPStatus.OK:
        raise HomeAssistantError
