"""Trigger an OBS alert when the channel gets raided."""

from TwitchInfoCommands.obs_helpers import (
    DEFAULT_SCENE_NAME,
    DEFAULT_VISIBLE_SECONDS,
    extract_username,
    launch_obs_alert,
    parse_irc_tags,
    write_text_file,
)


OBS_SCENE_NAME = DEFAULT_SCENE_NAME
OBS_SOURCE_NAME = "Raid"
SOURCE_VISIBLE_SECONDS = 10


def handle_raid(line: str) -> bool:
    """Trigger the raid OBS source for Twitch raid USERNOTICE events."""
    if 'USERNOTICE' not in line:
        return False

    tags = parse_irc_tags(line)
    if tags.get('msg-id') != 'raid':
        return False

    username = extract_username(line, tags)
    viewer_count = tags.get('msg-param-viewerCount', 'unknown')
    viewer_label = 'viewer' if str(viewer_count) == '1' else 'viewers'
    print(f"[Info] Raid detected from {username} with {viewer_count} viewer(s)")
    write_text_file('raid_info.txt', f"{username} ({viewer_count} {viewer_label})")
    launch_obs_alert('raid', OBS_SCENE_NAME, OBS_SOURCE_NAME, SOURCE_VISIBLE_SECONDS)
    return True
