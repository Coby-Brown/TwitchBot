"""Route Twitch IRC info events to OBS-backed alert handlers."""

from TwitchInfoCommands.cheer import handle_cheer
from TwitchInfoCommands.new_subscriber import handle_new_subscriber
from TwitchInfoCommands.raid import handle_raid


INFO_HANDLERS = (
    handle_cheer,
    handle_new_subscriber,
    handle_raid,
)


def handle_twitch_info_event(line: str) -> bool:
    """Run all matching Twitch info handlers for an incoming IRC line."""
    handled = False

    for handler in INFO_HANDLERS:
        try:
            handled = handler(line) or handled
        except Exception as exc:
            print(f"[Info] {handler.__name__} failed: {exc}")

    return handled
