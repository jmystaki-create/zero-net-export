"""Backup hooks for Zero Net Export."""
from __future__ import annotations

from homeassistant.core import HomeAssistant


async def async_pre_backup(hass: HomeAssistant) -> None:
    """Run before Home Assistant creates a backup."""
    return None


async def async_post_backup(hass: HomeAssistant) -> None:
    """Run after Home Assistant finishes creating a backup."""
    return None
