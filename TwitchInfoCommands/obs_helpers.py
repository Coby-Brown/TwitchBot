"""Shared OBS helpers for Twitch info event alerts."""

from __future__ import annotations

from pathlib import Path
import threading
import time

from connect_obs import connect as connect_obs


DEFAULT_SCENE_NAME = "Live"
DEFAULT_VISIBLE_SECONDS = 5
ROOT_DIR = Path(__file__).resolve().parents[1]
TEXT_FILES_DIR = ROOT_DIR / "ExtraFiles" / "TextBasedFiles"


def write_text_file(filename: str, contents: str) -> None:
    """Write plain-text status data for stream overlays."""
    TEXT_FILES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = TEXT_FILES_DIR / filename
    normalized_contents = contents.rstrip() if contents else ''
    file_path.write_text(f"{normalized_contents}\n", encoding='utf-8')


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


def _list_scene_names(client) -> list[str]:
    """Return all available OBS scene names."""
    try:
        scenes = client.get_scene_list().scenes
    except Exception:
        return []

    names: list[str] = []
    for scene in scenes:
        scene_name = scene.get('sceneName')
        if scene_name:
            names.append(scene_name)
    return names


def _resolve_scene_item(client, scene_name: str, source_name: str) -> tuple[str | None, int | None]:
    """Find the scene item id, falling back to the active/available scenes if needed."""
    if not source_name:
        return None, None

    available_scenes = _list_scene_names(client)
    candidate_scenes: list[str] = []

    if scene_name and scene_name in available_scenes:
        candidate_scenes.append(scene_name)

    try:
        current_scene_name = client.get_current_program_scene().current_program_scene_name
        if (
            current_scene_name
            and current_scene_name in available_scenes
            and current_scene_name not in candidate_scenes
        ):
            candidate_scenes.append(current_scene_name)
    except Exception:
        pass

    for available_scene in available_scenes:
        if available_scene not in candidate_scenes:
            candidate_scenes.append(available_scene)

    for candidate_scene in candidate_scenes:
        try:
            scene_items = client.get_scene_item_list(candidate_scene).scene_items
        except Exception:
            continue

        for scene_item in scene_items:
            if scene_item.get('sourceName') == source_name:
                scene_item_id = scene_item.get('sceneItemId')
                if scene_item_id is not None:
                    return candidate_scene, scene_item_id

    return None, None


def trigger_obs_source(
    scene_name: str,
    source_name: str,
    visible_seconds: int = DEFAULT_VISIBLE_SECONDS,
) -> None:
    """Enable an OBS source briefly, then hide it again."""
    client = None
    item_id = None
    resolved_scene_name = scene_name
    source_enabled = False

    try:
        client = connect_obs()
        resolved_scene_name, item_id = _resolve_scene_item(client, scene_name, source_name)

        if resolved_scene_name is None or item_id is None:
            available_scenes = ', '.join(_list_scene_names(client)) or 'none'
            print(
                f"[Info] OBS trigger skipped for '{source_name}': "
                f"no matching source was found for preferred scene '{scene_name}'. "
                f"Available scenes: {available_scenes}"
            )
            return

        if resolved_scene_name != scene_name:
            print(
                f"[Info] OBS source '{source_name}' was not found in '{scene_name}', "
                f"using '{resolved_scene_name}' instead."
            )

        client.set_scene_item_enabled(resolved_scene_name, item_id, True)
        source_enabled = True
        print(f"[Info] Enabled OBS source '{source_name}' in scene '{resolved_scene_name}'")
        time.sleep(visible_seconds)
    except Exception as exc:
        print(f"[Info] OBS trigger failed for '{source_name}': {exc}")
    finally:
        if client is not None and item_id is not None and source_enabled and resolved_scene_name:
            try:
                client.set_scene_item_enabled(resolved_scene_name, item_id, False)
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
