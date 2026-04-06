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


def handle_reward_redemption(line: str) -> bool:
    """Run the matching reward command for a Twitch IRC line, if any."""
    tags = _parse_irc_tags(line)
    reward_id = tags.get('custom-reward-id')
    if not reward_id:
        return False

    reward_command = REWARD_COMMANDS.get(reward_id)
    if reward_command is None:
        print(f"[Reward] No command mapped for reward id: {reward_id}")
        return False

    print(f"[Reward] Running reward command for id: {reward_id}")
    reward_command()
    return True
