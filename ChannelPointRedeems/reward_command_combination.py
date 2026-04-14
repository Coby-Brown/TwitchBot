"""Route Twitch channel point redemptions to reward commands."""

from ChannelPointRedeems.custom_reward_example import channel_point_example_command


# Replace this with your real Twitch custom reward ID.
EXAMPLE_CUSTOM_REWARD_ID = "replace-with-your-custom-reward-id"

REWARD_COMMANDS = {
    EXAMPLE_CUSTOM_REWARD_ID: channel_point_example_command,
}


def _parse_irc_tags(line: str) -> dict[str, str]:
    if not line.startswith('@'):
        return {}

    tags_part, _, _ = line.partition(' ')
    tags = {}
    for entry in tags_part[1:].split(';'):
        key, _, value = entry.partition('=')
        tags[key] = value
    return tags


def handle_reward_by_id(reward_id: str | None, reward_title: str | None = None) -> bool:
    """Run the matching reward command for a reward id or title."""
    normalized_id = reward_id.strip() if reward_id else ''
    normalized_title = reward_title.strip() if reward_title else ''

    reward_command = REWARD_COMMANDS.get(normalized_id)
    if reward_command is None and normalized_title:
        reward_command = REWARD_COMMANDS_BY_TITLE.get(normalized_title.casefold())

    if reward_command is None:
        if normalized_id or normalized_title:
            print(
                f"[Reward] No command mapped for reward id/title: "
                f"{normalized_id or 'unknown'} / {normalized_title or 'unknown'}"
            )
        return False

    print(f"[Reward] Running reward command for: {normalized_title or normalized_id}")
    reward_command(normalized_title or None)
    return True


def handle_reward_redemption(line: str) -> bool:
    """Run the matching reward command for a Twitch IRC line, if any."""
    tags = _parse_irc_tags(line)
    reward_id = tags.get('custom-reward-id')
    reward_title = tags.get('custom-reward-title')
    return handle_reward_by_id(reward_id, reward_title)
