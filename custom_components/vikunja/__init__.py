from datetime import timedelta

import httpx
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from pyvikunja.api import VikunjaAPI

from .const import DOMAIN, CONF_BASE_URL, CONF_TOKEN, LOGGER, CONF_SECS_INTERVAL
from .coordinator import VikunjaDataUpdateCoordinator

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DATETIME,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.NUMBER]


async def async_setup_entry(hass, entry):
    """Set up Vikunja from a config entry."""
    LOGGER.info("Starting Vikunja integration setup")

    base_url = entry.data.get(CONF_BASE_URL) or ""
    token = entry.data.get(CONF_TOKEN) or ""
    secs_interval = entry.data.get(CONF_SECS_INTERVAL) or 60

    if not base_url or not token:
        LOGGER.error("Base URL or token is missing")
        return False

    # Initialize Vikunja API client
    vikunja_api = VikunjaAPI(base_url, token)

    try:
        await vikunja_api.ping()
    except httpx.HTTPError as e:
        LOGGER.error(f"Error setting up Vikunja at {vikunja_api.web_ui_link}: {e}")
        raise e

    coordinator = VikunjaDataUpdateCoordinator(hass, entry.entry_id, vikunja_api, secs_interval)
    await coordinator.async_config_entry_first_refresh()

    # Update the entry title to include the host
    new_title = f"Vikunja ({vikunja_api.web_ui_link})"
    if entry.title != new_title:
        hass.config_entries.async_update_entry(entry, title=new_title)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": vikunja_api,
        "coordinator": coordinator
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    LOGGER.info("Vikunja setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove Vikunja integration."""
    hass.data[DOMAIN].pop(entry.entry_id, None)

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
