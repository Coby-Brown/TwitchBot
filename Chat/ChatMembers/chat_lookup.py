import json
import os
import threading
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ConfigFiles import channel_info
from ConfigFiles import tokens


CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'chat_lookup_cache.json')
FOLLOWER_LOOKUP_TTL_SECONDS = 6 * 60 * 60
_CACHE_LOCK = threading.Lock()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso8601(value: str):
    if not value:
        return None

    try:
        # Twitch returns timestamps like 2024-05-10T18:20:11Z.
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def _safe_json_load(path: str):
    if not os.path.exists(path):
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _safe_json_save(path: str, data):
    tmp_path = f"{path}.tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def _parse_irc_tags(raw_line: str):
    if not raw_line.startswith('@'):
        return {}

    tag_blob = raw_line.split(' ', 1)[0][1:]
    tags = {}
    for part in tag_blob.split(';'):
        key, _, value = part.partition('=')
        tags[key] = value
    return tags


def _parse_badges(badge_blob: str):
    badges = {}
    if not badge_blob:
        return badges

    for badge_pair in badge_blob.split(','):
        key, _, value = badge_pair.partition('/')
        if key:
            badges[key] = value
    return badges


def _oauth_bearer(token_value: str):
    token_value = token_value.strip()
    if token_value.startswith('oauth:'):
        return token_value.split(':', 1)[1]
    return token_value


def _fetch_follow_data(user_id: str):
    bearer = _oauth_bearer(tokens.BROADCASTER_TOKEN)
    query = urlencode({'broadcaster_id': channel_info.USER_ID, 'user_id': user_id})
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
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {
            'is_follower': None,
            'followed_at': None,
            'follower_length_days': None,
            'follower_length_text': None,
            'follower_lookup_error': True,
        }

    rows = payload.get('data', [])
    if not rows:
        return {
            'is_follower': False,
            'followed_at': None,
            'follower_length_days': 0,
            'follower_length_text': 'not_following',
            'follower_lookup_error': False,
        }

    followed_at = rows[0].get('followed_at')
    followed_dt = _parse_iso8601(followed_at)
    if not followed_dt:
        return {
            'is_follower': True,
            'followed_at': followed_at,
            'follower_length_days': None,
            'follower_length_text': None,
            'follower_lookup_error': False,
        }

    age_days = max((_now_utc() - followed_dt).days, 0)
    return {
        'is_follower': True,
        'followed_at': followed_at,
        'follower_length_days': age_days,
        'follower_length_text': f'{age_days}d',
        'follower_lookup_error': False,
    }


def _base_member_info_from_tags(tags):
    badges = _parse_badges(tags.get('badges', ''))
    sub_tier = badges.get('subscriber')

    return {
        'username': tags.get('display-name') or tags.get('login') or '',
        'user_id': tags.get('user-id') or '',
        'is_subscriber': tags.get('subscriber') == '1' or 'subscriber' in badges,
        'sub_tier': sub_tier,
        'sub_months': (tags.get('badge-info') or '').split('subscriber/', 1)[1].split(',', 1)[0]
        if 'subscriber/' in (tags.get('badge-info') or '')
        else None,
        'is_prime': 'premium' in badges,
        'badges': badges,
    }


def _cache_key(member_info):
    if member_info.get('user_id'):
        return member_info['user_id']
    return member_info.get('username', '').lower()


def lookup_member_info(raw_irc_line: str, use_cache: bool = True):
    tags = _parse_irc_tags(raw_irc_line)
    if not tags:
        return {}

    member = _base_member_info_from_tags(tags)
    key = _cache_key(member)
    if not key:
        return member

    with _CACHE_LOCK:
        cache_data = _safe_json_load(CACHE_FILE_PATH)
        cached = cache_data.get(key)

        if use_cache and cached:
            cached_at = cached.get('cached_at_epoch', 0)
            if (time.time() - cached_at) < FOLLOWER_LOOKUP_TTL_SECONDS:
                merged = dict(cached)
                merged.update(member)
                return merged

    follow_data = _fetch_follow_data(member['user_id']) if member.get('user_id') else {
        'is_follower': None,
        'followed_at': None,
        'follower_length_days': None,
        'follower_length_text': None,
        'follower_lookup_error': False,
    }

    result = {
        **member,
        **follow_data,
        'cached_at_epoch': int(time.time()),
    }

    with _CACHE_LOCK:
        cache_data = _safe_json_load(CACHE_FILE_PATH)
        cache_data[key] = result
        _safe_json_save(CACHE_FILE_PATH, cache_data)

    return result


def clear_cache():
    with _CACHE_LOCK:
        _safe_json_save(CACHE_FILE_PATH, {})
