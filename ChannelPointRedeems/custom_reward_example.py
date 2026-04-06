"""Example channel point reward command.

Update the values below to match your OBS scene/source and the sound file you
want to play when the reward is redeemed.
"""

from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from connect_obs import connect as connect_obs


REWARD_TITLE = "celebration time"
OBS_SCENE_NAME = "Alerts"
OBS_SOURCE_NAME = "Channel Point Alert"
SOUND_FILE = Path(__file__).resolve().parent / "sounds" / "reward-alert.mp3"
SOURCE_VISIBLE_SECONDS = 3


def play_sound_file(sound_file: Path) -> None:
    """Play a local sound file on the bot machine."""
    if not sound_file.exists():
        print(f"[Reward] Sound file not found: {sound_file}")
        return

    player_commands = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(sound_file)],
        ["paplay", str(sound_file)],
        ["aplay", str(sound_file)],
    ]

    for command in player_commands:
        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"[Reward] Playing sound: {sound_file.name}")
            return
        except FileNotFoundError:
            continue

    print("[Reward] No supported audio player found. Install ffplay, paplay, or aplay.")


def trigger_obs_source(scene_name: str, source_name: str, visible_seconds: int = SOURCE_VISIBLE_SECONDS) -> None:
    """Enable an OBS source briefly, then hide it again."""
    client = None
    item_id = None
    source_enabled = False

    try:
        client = connect_obs()
        scene_item = client.get_scene_item_id(scene_name, source_name)
        item_id = scene_item.scene_item_id

        client.set_scene_item_enabled(scene_name, item_id, True)
        source_enabled = True
        print(f"[Reward] Enabled OBS source '{source_name}' in scene '{scene_name}'")
        time.sleep(visible_seconds)
    except Exception as exc:
        print(f"[Reward] OBS trigger failed: {exc}")
    finally:
        if client is not None and item_id is not None and source_enabled:
            try:
                client.set_scene_item_enabled(scene_name, item_id, False)
                print(f"[Reward] Disabled OBS source '{source_name}'")
            except Exception as exc:
                print(f"[Reward] Could not disable OBS source: {exc}")

        if client is not None:
            client.disconnect()


def channel_point_example_command(reward_title: str | None = None) -> bool:
    """Example reward handler that combines a sound effect with an OBS action."""
    if reward_title is not None and reward_title.strip().casefold() != REWARD_TITLE.casefold():
        return False

    threading.Thread(target=play_sound_file, args=(SOUND_FILE,)).start()
    threading.Thread(
        target=trigger_obs_source,
        args=(OBS_SCENE_NAME, OBS_SOURCE_NAME, SOURCE_VISIBLE_SECONDS),
    ).start()
    return True


if __name__ == "__main__":
    # Quick manual test:
    # /home/coby-brown/Documents/Programs/TwitchBot/.venv/bin/python ChannelPointRedeems/custom_reward_example.py
    channel_point_example_command(REWARD_TITLE)
