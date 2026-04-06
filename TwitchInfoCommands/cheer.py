"""Trigger an OBS alert when someone cheers with bits."""

from TwitchInfoCommands.obs_helpers import (
    DEFAULT_SCENE_NAME,
    DEFAULT_VISIBLE_SECONDS,
    extract_username,
    launch_obs_alert,
    parse_irc_tags,
)


OBS_SCENE_NAME = DEFAULT_SCENE_NAME
OBS_SOURCE_NAME = "Cheer Alert"
SOURCE_VISIBLE_SECONDS = DEFAULT_VISIBLE_SECONDS


def handle_cheer(line: str) -> bool:
    """Trigger the cheer OBS source for Twitch bit donations."""
    if 'PRIVMSG' not in line:
        return False

    tags = parse_irc_tags(line)
    bits_text = tags.get('bits')
    if not bits_text:
        return False

    try:
        bits_value = int(bits_text)
    except ValueError:
        return False

    if bits_value <= 0:
        return False

    username = extract_username(line, tags)
    print(f"[Info] Cheer detected from {username} ({bits_value} bits)")
    launch_obs_alert('cheer', OBS_SCENE_NAME, OBS_SOURCE_NAME, SOURCE_VISIBLE_SECONDS)
    return True
