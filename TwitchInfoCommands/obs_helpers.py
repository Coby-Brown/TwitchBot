"""Shared OBS helpers for Twitch info event alerts."""

from __future__ import annotations

import threading
import time

from connect_obs import connect as connect_obs


DEFAULT_SCENE_NAME = "Streaming"
DEFAULT_VISIBLE_SECONDS = 5


def parse_irc_tags(line: str) -> dict[str, str]:
    """Parse the IRC tag prefix from a Twitch line."""
    if not line.startswith('@'):
        return {}

    tags_part, _, _ = line.partition(' ')
    tags: dict[str, str] = {}
    for entry in tags_part[1:].split(';'):
        key, _, value = entry.partition('=')
        tags[key] = value
    return tags


def extract_username(line: str, tags: dict[str, str] | None = None) -> str:
    """Best-effort username extraction for info events."""
    tags = tags or parse_irc_tags(line)

    for key in ('display-name', 'login', 'msg-param-displayName', 'msg-param-login'):
        value = tags.get(key)
        if value:
            return value

    raw = line
    if raw.startswith('@'):
        _, _, raw = raw.partition(' ')

    if raw.startswith(':') and '!' in raw:
        return raw[1:].split('!', 1)[0]

    return 'unknown'


def trigger_obs_source(
    scene_name: str,
    source_name: str,
    visible_seconds: int = DEFAULT_VISIBLE_SECONDS,
) -> None:
    """Enable an OBS source briefly, then hide it again."""
    client = None
    item_id = None
    source_enabled = False

    try:
        client = connect_obs()
        scene_item = client.get_scene_item_id(scene_name, source_name)
        item_id = scene_item.scene_item_id

        client.set_scene_item_enabled(scene_name, item_id, True)
        source_enabled = True
        print(f"[Info] Enabled OBS source '{source_name}' in scene '{scene_name}'")
        time.sleep(visible_seconds)
    except Exception as exc:
        print(f"[Info] OBS trigger failed for '{source_name}': {exc}")
    finally:
        if client is not None and item_id is not None and source_enabled:
            try:
                client.set_scene_item_enabled(scene_name, item_id, False)
                print(f"[Info] Disabled OBS source '{source_name}'")
            except Exception as exc:
                print(f"[Info] Could not disable OBS source '{source_name}': {exc}")

        if client is not None:
            client.disconnect()


def launch_obs_alert(
    alert_name: str,
    scene_name: str,
    source_name: str,
    visible_seconds: int = DEFAULT_VISIBLE_SECONDS,
) -> None:
    """Run an OBS alert in a daemon thread so chat processing stays responsive."""
    thread_name = f"obs-{alert_name.lower().replace(' ', '-')}-alert"
    threading.Thread(
        target=trigger_obs_source,
        args=(scene_name, source_name, visible_seconds),
        daemon=True,
        name=thread_name,
    ).start()
