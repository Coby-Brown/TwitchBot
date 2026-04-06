"""Follower alert helper.

Twitch IRC does not emit real follow events, so this function is ready to be
called from a future EventSub/webhook integration.
"""

from TwitchInfoCommands.obs_helpers import (
    DEFAULT_SCENE_NAME,
    DEFAULT_VISIBLE_SECONDS,
    launch_obs_alert,
)


OBS_SCENE_NAME = DEFAULT_SCENE_NAME
OBS_SOURCE_NAME = "Follower Alert"
SOURCE_VISIBLE_SECONDS = DEFAULT_VISIBLE_SECONDS


def handle_new_follower(username: str | None = None) -> bool:
    """Trigger the follower OBS source when a new follow is detected elsewhere."""
    follower_name = username.strip() if username else 'a new follower'
    print(f"[Info] Follower detected: {follower_name}")
    launch_obs_alert('follower', OBS_SCENE_NAME, OBS_SOURCE_NAME, SOURCE_VISIBLE_SECONDS)
    return True
