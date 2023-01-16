"""Provide diagnostics for Matter."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from matter_server.common.helpers.util import dataclass_to_dict

from homeassistant.components.diagnostics import REDACTED
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .helpers import get_matter

ATTRIBUTE_TO_REDACT = {"chip.clusters.Objects.Basic.Attributes.Location"}


def redact_matter_attribute(node_data: dict[str, Any]) -> dict[str, Any]:
    """Redact Matter cluster attribute."""
    redacted = deepcopy(node_data)
    for attribute_to_redact in ATTRIBUTE_TO_REDACT:
        for value in redacted["attributes"].values():
            if value["attribute_type"] == attribute_to_redact:
                value["value"] = REDACTED

    return redacted


def remove_serialization_type(data: dict[str, Any]) -> dict[str, Any]:
    """Remove serialization type from data."""
    if "_type" in data:
        data.pop("_type")
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    matter = get_matter(hass)
    server_diagnostics = await matter.matter_client.get_diagnostics()
    data = remove_serialization_type(dataclass_to_dict(server_diagnostics))
    nodes = [redact_matter_attribute(node_data) for node_data in data["nodes"]]
    data["nodes"] = nodes

    return {"server": data}


async def async_get_device_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry, device: dr.DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device."""
    matter = get_matter(hass)
    unique_id = next(
        identifier[1] for identifier in device.identifiers if identifier[0] == DOMAIN
    )

    node = next(
        node
        for node in await matter.matter_client.get_nodes()
        if node.unique_id == unique_id
    )

    server_diagnostics = await matter.matter_client.get_diagnostics()

    return {
        "server_info": remove_serialization_type(
            dataclass_to_dict(server_diagnostics.info)
        ),
        "node": redact_matter_attribute(
            remove_serialization_type(dataclass_to_dict(node))
        ),
    }
