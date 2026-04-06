"""Trigger an OBS alert when the channel gets raided."""

from TwitchInfoCommands.obs_helpers import (
    DEFAULT_SCENE_NAME,
    DEFAULT_VISIBLE_SECONDS,
    extract_username,
    launch_obs_alert,
    parse_irc_tags,
)


OBS_SCENE_NAME = DEFAULT_SCENE_NAME
OBS_SOURCE_NAME = "Raid Alert"
SOURCE_VISIBLE_SECONDS = DEFAULT_VISIBLE_SECONDS


def handle_raid(line: str) -> bool:
    """Trigger the raid OBS source for Twitch raid USERNOTICE events."""
    if 'USERNOTICE' not in line:
        return False

    tags = parse_irc_tags(line)
    if tags.get('msg-id') != 'raid':
        return False

    username = extract_username(line, tags)
    viewer_count = tags.get('msg-param-viewerCount', 'unknown')
    print(f"[Info] Raid detected from {username} with {viewer_count} viewer(s)")
    launch_obs_alert('raid', OBS_SCENE_NAME, OBS_SOURCE_NAME, SOURCE_VISIBLE_SECONDS)
    return True
