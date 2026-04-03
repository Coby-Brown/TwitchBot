import html
from typing import Any, Dict, List

from Chat.ChatMembers import chat_lookup


# Update these rules to customize how chatters are styled in HTML output.
# Rules are evaluated top-to-bottom, and later matches override earlier styles.
STYLE_RULES: List[Dict[str, Any]] = [
	{
		'name': 'lead_moderator',
		'conditions': [
			{'field': 'badges.lead_moderator', 'equals': '1'},
		],
		'styles': {
			'username': 'color: #f59e0b; font-weight: 700; letter-spacing: 0.03em;',
			'message': 'color: #f8fafc;',
		},
	},
	{
		'name': 'subscriber',
		'conditions': [
			{'field': 'is_subscriber', 'equals': True},
		],
		'styles': {
			'username': 'color: #22c55e; font-weight: 700;',
		},
	},
	{
		'name': 'prime_user',
		'conditions': [
			{'field': 'is_prime', 'equals': True},
		],
		'styles': {
			'username': 'color: #38bdf8; font-weight: 700;',
		},
	},
	{
		'name': 'long_term_follower',
		'conditions': [
			{'field': 'follower_length_days', 'gte': 30},
		],
		'styles': {
			'username': 'color: #a78bfa; font-weight: 700;',
		},
	},
]


DEFAULT_STYLES: Dict[str, str] = {
	'paragraph': 'margin: 0.25rem 0; font-family: Verdana, sans-serif; font-size: 14px;',
	'username': 'color: #e5e7eb; font-weight: 600;',
	'message': 'color: #f1f5f9;',
}


def _get_nested(data: Dict[str, Any], field_path: str):
	current: Any = data
	for key in field_path.split('.'):
		if not isinstance(current, dict):
			return None
		current = current.get(key)
	return current


def _matches_condition(member_info: Dict[str, Any], condition: Dict[str, Any]) -> bool:
	value = _get_nested(member_info, condition.get('field', ''))

	if 'equals' in condition:
		return value == condition['equals']

	if value is None:
		return False

	if 'gte' in condition:
		return value >= condition['gte']
	if 'lte' in condition:
		return value <= condition['lte']
	if 'contains' in condition:
		return condition['contains'] in value

	return False


def _matches_rule(member_info: Dict[str, Any], rule: Dict[str, Any]) -> bool:
	conditions = rule.get('conditions', [])
	return all(_matches_condition(member_info, condition) for condition in conditions)


def _cache_key(member_info: Dict[str, Any]) -> str:
	user_id = member_info.get('user_id')
	if user_id:
		return str(user_id)
	return str(member_info.get('username', '')).lower()


def _load_cached_member_info(member_info: Dict[str, Any]) -> Dict[str, Any]:
	key = _cache_key(member_info)
	if not key:
		return member_info

	cache_data = chat_lookup._safe_json_load(chat_lookup.CACHE_FILE_PATH)
	cached = cache_data.get(key, {})

	merged = dict(cached)
	merged.update(member_info)
	return merged


def resolve_member_styles(member_info: Dict[str, Any]) -> Dict[str, str]:
	merged_info = _load_cached_member_info(member_info)
	styles = dict(DEFAULT_STYLES)

	for rule in STYLE_RULES:
		if _matches_rule(merged_info, rule):
			styles.update(rule.get('styles', {}))

	return styles


def build_html_line(username: str, message: str, member_info: Dict[str, Any]) -> str:
	styles = resolve_member_styles(member_info)

	safe_username = html.escape(username)
	safe_message = html.escape(message)
	paragraph_style = styles.get('paragraph', '')
	username_style = styles.get('username', '')
	message_style = styles.get('message', '')

	return (
		f"<p style=\"{paragraph_style}\">"
		f"<span style=\"{username_style}\">{safe_username}</span>: "
		f"<span style=\"{message_style}\">{safe_message}</span>"
		"</p>"
	)
