from Chat import file_writer
from ChannelPointRedeems.reward_command_combination import handle_reward_redemption
from ChannelPointRedeems.reward_listener import start_reward_listener
from TwitchInfoCommands.handler import handle_twitch_info_event
from TwitchInfoCommands.new_follower import start_follower_listener
from audio_sink import ensure_audio_sink
from chat_refresh import start_refresh_thread
from connect_twitch import connect as connect_twitch


def handle_incoming_line(line: str) -> None:
    """Run all configured handlers for each raw Twitch IRC line."""
    handle_reward_redemption(line)
    handle_twitch_info_event(line)


def main():
    # Create the dedicated TwitchBot audio sink once before any alerts can play.
    ensure_audio_sink()

    # Connect once, start OBS browser refreshing, and let a single reader write all outputs.
    sock = connect_twitch()
    start_refresh_thread()
    start_follower_listener()
    start_reward_listener()
    file_writer.write_messages(sock, reward_handler=handle_incoming_line)


if __name__ == '__main__':
    main()