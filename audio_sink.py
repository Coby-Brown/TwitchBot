"""Create and configure a dedicated audio sink for TwitchBot on Linux."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Final

SINK_NAME: Final = "TwitchBot_Audio"
SINK_DESCRIPTION: Final = "TwitchBot_Audio"

_configured = False


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run an audio-control command and capture the result."""
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def _sink_exists(sink_name: str) -> bool:
    """Return True when the named PulseAudio/PipeWire sink already exists."""
    if shutil.which("pactl") is not None:
        result = _run_command(["pactl", "list", "short", "sinks"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Unable to list audio sinks with pactl.")

        for line in result.stdout.splitlines():
            columns = line.split()
            if len(columns) > 1 and columns[1] == sink_name:
                return True
        return False

    if shutil.which("pw-cli") is not None:
        result = _run_command(["pw-cli", "ls", "Node"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Unable to list PipeWire nodes.")
        return f'node.name = "{sink_name}"' in result.stdout

    raise RuntimeError("No supported audio control command found.")


def _create_sink(sink_name: str) -> None:
    """Create the named null sink using PulseAudio or PipeWire tooling."""
    if shutil.which("pactl") is not None:
        result = _run_command(
            [
                "pactl",
                "load-module",
                "module-null-sink",
                f"sink_name={sink_name}",
                f"sink_properties=device.description={SINK_DESCRIPTION}",
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Could not create audio sink with pactl.")
        return

    if shutil.which("pw-cli") is not None:
        properties = (
            "{ "
            "factory.name = support.null-audio-sink "
            f'node.name = "{sink_name}" '
            f'node.description = "{SINK_DESCRIPTION}" '
            'media.class = "Audio/Sink" '
            "object.linger = true "
            "audio.position = [ FL FR ] "
            "}"
        )
        result = _run_command(["pw-cli", "create-node", "adapter", properties])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Could not create audio sink with pw-cli.")
        return

    raise RuntimeError("Install `pactl` or PipeWire (`pw-cli`) to create an audio sink.")


def ensure_audio_sink(sink_name: str = SINK_NAME) -> bool:
    """Ensure the TwitchBot audio sink exists and route this process to it."""
    global _configured

    if _configured and os.environ.get("PULSE_SINK") == sink_name:
        return True

    if shutil.which("pactl") is None and shutil.which("pw-cli") is None:
        print("[Audio] No supported sink tool was found. Install `pactl` or `pw-cli`.")
        return False

    try:
        if _sink_exists(sink_name):
            print(f"[Audio] Using existing audio sink: {sink_name}")
        else:
            _create_sink(sink_name)
            print(f"[Audio] Created audio sink: {sink_name}")

        os.environ["PULSE_SINK"] = sink_name
        pipewire_target = f"node.target={sink_name}"
        existing_pipewire_props = os.environ.get("PIPEWIRE_PROPS", "").strip()
        if pipewire_target not in existing_pipewire_props.split():
            os.environ["PIPEWIRE_PROPS"] = f"{existing_pipewire_props} {pipewire_target}".strip()
        os.environ.setdefault("SDL_AUDIODRIVER", "pulseaudio")
        _configured = True
        print(f"[Audio] Routing TwitchBot audio to sink: {sink_name}")
        return True
    except Exception as exc:
        print(f"[Audio] Could not configure sink '{sink_name}': {exc}")
        return False


if __name__ == "__main__":
    ensure_audio_sink()
