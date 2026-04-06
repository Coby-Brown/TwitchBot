"""Poll Twitch follower data and trigger an OBS alert for new followers."""

from __future__ import annotations

import json
import os
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ConfigFiles import channel_info
from ConfigFiles import tokens
from TwitchInfoCommands.obs_helpers import (
    DEFAULT_SCENE_NAME,
    DEFAULT_VISIBLE_SECONDS,
    launch_obs_alert,
    write_text_file,
)


OBS_SCENE_NAME = DEFAULT_SCENE_NAME
OBS_SOURCE_NAME = "Follower"
SOURCE_VISIBLE_SECONDS = DEFAULT_VISIBLE_SECONDS
FOLLOWER_POLL_INTERVAL = 15
FOLLOWER_FETCH_LIMIT = 25
HTTP_TIMEOUT_SECONDS = 10
FOLLOWER_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ExtraFiles', 'Cache')
FOLLOWER_CACHE_PATH = os.path.join(FOLLOWER_CACHE_DIR, 'follower_cache.json')
_STATE_LOCK = threading.Lock()


def _safe_json_load(path: str) -> dict:
    if not os.path.exists(path):
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as file_handle:
            payload = json.load(file_handle)
            return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _safe_json_save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, 'w', encoding='utf-8') as file_handle:
        json.dump(data, file_handle, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def _oauth_bearer(token_value: str) -> str:
    token_value = token_value.strip()
    if token_value.startswith('oauth:'):
        return token_value.split(':', 1)[1]
    return token_value


def _get_api_auth() -> tuple[str, str]:
    broadcaster_token = getattr(tokens, 'BROADCASTER_TOKEN', '').strip()
    if broadcaster_token:
        return _oauth_bearer(broadcaster_token), channel_info.USER_ID

    fallback_token = getattr(tokens, 'TOKEN', '').strip()
    moderator_id = getattr(tokens, 'BOT_USER_ID', '').strip() or channel_info.USER_ID
    return _oauth_bearer(fallback_token), moderator_id


def _fetch_recent_followers(limit: int = FOLLOWER_FETCH_LIMIT) -> list[dict]:
    bearer, moderator_id = _get_api_auth()
    if not bearer:
        print('[Info] Follower polling skipped: missing Twitch API token.')
        return []

    query = urlencode(
        {
            'broadcaster_id': channel_info.USER_ID,
            'moderator_id': moderator_id,
            'first': max(1, min(limit, 100)),
        }
    )
    url = f"https://api.twitch.tv/helix/channels/followers?{query}"
    request = Request(
        url,
        headers={
            'Client-Id': tokens.CLIENT_ID,
            'Authorization': f'Bearer {bearer}',
        },
        method='GET',
    )

    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='ignore')
        print(f"[Info] Follower poll HTTP error {exc.code}: {error_body}")
        return []
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[Info] Follower poll failed: {exc}")
        return []

    rows = payload.get('data', [])
    return rows if isinstance(rows, list) else []


def handle_new_follower(username: str | None = None) -> bool:
    """Trigger the follower OBS source for a newly detected follower."""
    follower_name = username.strip() if username else 'a new follower'
    print(f"[Info] Follower detected: {follower_name}")
    write_text_file('latest_follower.txt', follower_name)
    launch_obs_alert('follower', OBS_SCENE_NAME, OBS_SOURCE_NAME, SOURCE_VISIBLE_SECONDS)
    return True


def poll_for_new_followers(poll_interval: float = FOLLOWER_POLL_INTERVAL) -> None:
    """Continuously poll Twitch for recent follows and alert on new ones only."""
    poll_interval = max(float(poll_interval), 5.0)

    with _STATE_LOCK:
        state = _safe_json_load(FOLLOWER_CACHE_PATH)
        last_seen_user_id = state.get('last_seen_user_id')

    while True:
        followers = _fetch_recent_followers(FOLLOWER_FETCH_LIMIT)
        if followers:
            newest_follower = followers[0]
            newest_user_id = newest_follower.get('user_id')

            if not last_seen_user_id:
                last_seen_user_id = newest_user_id
                if newest_user_id:
                    with _STATE_LOCK:
                        _safe_json_save(FOLLOWER_CACHE_PATH, {'last_seen_user_id': newest_user_id})
                follower_name = newest_follower.get('user_name') or newest_follower.get('user_login') or 'unknown'
                write_text_file('latest_follower.txt', follower_name)
                print(f"[Info] Follower watcher primed at {follower_name}")
            else:
                new_followers = []
                for follower in followers:
                    if follower.get('user_id') == last_seen_user_id:
                        break
                    new_followers.append(follower)

                if new_followers:
                    for follower in reversed(new_followers):
                        follower_name = follower.get('user_name') or follower.get('user_login') or 'a new follower'
                        handle_new_follower(follower_name)

                    if newest_user_id:
                        last_seen_user_id = newest_user_id
                        with _STATE_LOCK:
                            _safe_json_save(FOLLOWER_CACHE_PATH, {'last_seen_user_id': newest_user_id})

        time.sleep(poll_interval)


def start_follower_listener(poll_interval: float = FOLLOWER_POLL_INTERVAL):
    """Start the background follower polling thread."""
    follower_thread = threading.Thread(
        target=poll_for_new_followers,
        args=(poll_interval,),
        daemon=True,
        name='twitch-follower-watch',
    )
    follower_thread.start()
    print(f"[Info] Follower watcher started (poll every {poll_interval:g}s)")
    return follower_thread
