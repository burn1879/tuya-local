"""
Mixins to make writing new platforms easier
"""
import logging
from homeassistant.const import (
    AREA_SQUARE_METERS,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    UnitOfTemperature,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory

from custom_components.tuya_local import DOMAIN, CONF_DEVICE_ID, CONF_IS_GATEWAY

_LOGGER = logging.getLogger(__name__)


@callback
def async_config_entry_by_device_id(hass, device_id):
    """Look up config entry by device id."""
    current_entries = hass.config_entries.async_entries(DOMAIN)
    for entry in current_entries:
        if entry.data[CONF_DEVICE_ID] == device_id:
            return entry
    return None


@callback
def async_config_entry_gateway(hass):
    """Look up gateway config entry."""
    current_entries = hass.config_entries.async_entries(DOMAIN)
    entries = set()
    for entry in current_entries:
        if CONF_IS_GATEWAY in entry.data and entry.data[CONF_IS_GATEWAY]:
            entries.add(entry.data[CONF_DEVICE_ID])

    return list(entries)


class TuyaLocalEntity:
    """Common functions for all entity types."""

    def _init_begin(self, device, config):
        self._device = device
        self._config = config
        self._attr_dps = []
        return {c.name: c for c in config.dps()}

    def _init_end(self, dps):
        for d in dps.values():
            if not d.hidden:
                self._attr_dps.append(d)

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._device.has_returned_state

    @property
    def name(self):
        """Return the name for the UI."""
        return self._config.name

    @property
    def has_entity_name(self):
        return True

    @property
    def unique_id(self):
        """Return the unique id for this entity."""
        return self._config.unique_id(self._device.unique_id)

    @property
    def device_info(self):
        """Return the device's information."""
        return self._device.device_info

    @property
    def entity_category(self):
        """Return the entitiy's category."""
        return (
            None
            if self._config.entity_category is None
            else EntityCategory(self._config.entity_category)
        )

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        icon = self._config.icon(self._device)
        if icon:
            return icon
        else:
            return super().icon

    @property
    def extra_state_attributes(self):
        """Get additional attributes that the platform itself does not support."""
        attr = {}
        for a in self._attr_dps:
            value = a.get_value(self._device)
            if value is not None or not a.optional:
                attr[a.name] = value
        return attr

    async def async_update(self):
        await self._device.async_refresh()

    async def async_added_to_hass(self):
        self._device.register_entity(self)

    async def async_will_remove_from_hass(self):
        await self._device.async_unregister_entity(self)


UNIT_ASCII_MAP = {
    "C": UnitOfTemperature.CELSIUS,
    "F": UnitOfTemperature.FAHRENHEIT,
    "ugm3": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    "m2": AREA_SQUARE_METERS,
}


def unit_from_ascii(unit):
    if unit in UNIT_ASCII_MAP:
        return UNIT_ASCII_MAP[unit]

    return unit
