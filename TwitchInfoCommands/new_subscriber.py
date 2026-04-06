"""Trigger an OBS alert for Twitch subscription events."""

from TwitchInfoCommands.obs_helpers import (
    DEFAULT_SCENE_NAME,
    DEFAULT_VISIBLE_SECONDS,
    extract_username,
    launch_obs_alert,
    parse_irc_tags,
)


OBS_SCENE_NAME = DEFAULT_SCENE_NAME
OBS_SOURCE_NAME = "Subscriber Alert"
SOURCE_VISIBLE_SECONDS = DEFAULT_VISIBLE_SECONDS
SUBSCRIPTION_EVENT_IDS = {
    'sub',
    'resub',
    'subgift',
    'anonsubgift',
    'submysterygift',
    'anonsubmysterygift',
    'giftpaidupgrade',
    'primepaidupgrade',
    'extendsub',
}


def handle_new_subscriber(line: str) -> bool:
    """Trigger the subscriber OBS source for Twitch USERNOTICE sub events."""
    if 'USERNOTICE' not in line:
        return False

    tags = parse_irc_tags(line)
    msg_id = tags.get('msg-id', '')
    if msg_id not in SUBSCRIPTION_EVENT_IDS:
        return False

    username = extract_username(line, tags)
    months = tags.get('msg-param-cumulative-months') or '1'
    print(f"[Info] Subscription event '{msg_id}' from {username} (months: {months})")
    launch_obs_alert('subscriber', OBS_SCENE_NAME, OBS_SOURCE_NAME, SOURCE_VISIBLE_SECONDS)
    return True
