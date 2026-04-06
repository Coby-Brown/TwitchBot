# TwitchBot

A Python Twitch bot for **live chat capture**, **OBS overlay updates**, and **stream event alerts**.

It connects to Twitch IRC, writes chat to text/HTML overlay files, refreshes an OBS browser source automatically, polls for new followers, and triggers OBS alerts for subscriptions, raids, cheers, and channel point rewards.

---

## Features

- 💬 **Live Twitch chat capture**
  - Writes raw chat to `ExtraFiles/TextBasedFiles/Chats/UnfilteredChat/`
  - Writes filtered chat to `ExtraFiles/TextBasedFiles/Chats/FilteredChat/`
- 🎨 **Styled HTML chat overlay**
  - Applies follower / subscriber / moderator styling rules
- 🔄 **OBS browser source auto-refresh**
  - Refreshes the `Chat` browser source on a timer
- 🔔 **Stream event alerts**
  - New follower polling
  - New subscriber alerts
  - Raid alerts
  - Cheer alerts
- 🎁 **Channel point reward hooks**
  - Example reward command included
- 🧠 **Basic chatter caching**
  - Stores follower/member lookup data in `ExtraFiles/Cache/`

---

## Project Structure

| Path | Purpose |
|---|---|
| `main.py` | Bot entry point |
| `connect_twitch.py` | Connects to Twitch IRC |
| `connect_obs.py` | Connects to OBS WebSocket |
| `chat_refresh.py` | Auto-refreshes an OBS browser source |
| `Chat/file_writer.py` | Reads IRC messages and writes overlay files |
| `Chat/ChatFilters/` | Message filtering logic |
| `Chat/ChatMembers/` | Chat member lookup and HTML styling |
| `TwitchInfoCommands/` | Follower / sub / raid / cheer alert handlers |
| `ChannelPointRedeems/` | Channel point reward routing and examples |
| `ConfigFiles/` | Channel and token configuration |
| `ExtraFiles/` | Cache files and generated overlay text/HTML |
| `Setup/setup.sh` | Linux/macOS setup helper |

---

## Requirements

- **Python 3.10+**
- **OBS Studio** with **WebSocket** enabled (default: `localhost:4455`)
- A **Twitch bot/moderator account**
- A **Twitch broadcaster token** for follower-related API calls

Python dependency:

- `obsws-python`

---

## Setup

### 1) Create the virtual environment and install dependencies

From the repository root:

```bash
bash Setup/setup.sh
source .venv/bin/activate
```

If you prefer manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Setup/requirements.txt
```

### 2) Configure Twitch credentials

Edit `ConfigFiles/tokens.py` and set:

- `TOKEN` — bot OAuth token
- `BROADCASTER_TOKEN` — broadcaster OAuth token
- `NICK` — bot username
- `CLIENT_ID` — Twitch application client ID
- `BOT_USER_ID` — bot account user ID
- `CLIENT_SECRET` — optional
- `OBS_WEBSOCKET_PASSWORD` — OBS WebSocket password if enabled

A template is included in `ConfigFiles/EXAMPLE:tokens.py`.

### 3) Configure the target channel

Edit `ConfigFiles/channel_info.py`:

```py
CHANNEL = 'your_channel_name'
USER_ID = 'your_twitch_user_id'
```

### 4) Match your OBS scene/source names

By default, the bot expects these OBS items to exist:

| Feature | Scene | Source |
|---|---|---|
| Chat browser refresh | n/a | `Chat` |
| Follower alert | `Streaming` | `Follower` |
| Subscriber alert | `Streaming` | `Subscriber Alert` |
| Raid alert | `Streaming` | `Raid` |
| Cheer alert | `Streaming` | `Cheer Alert` |
| Example channel point reward | `Alerts` | `Channel Point Alert` |

If your scene/source names differ, update the constants in:

- `chat_refresh.py`
- `TwitchInfoCommands/new_follower.py`
- `TwitchInfoCommands/new_subscriber.py`
- `TwitchInfoCommands/raid.py`
- `TwitchInfoCommands/cheer.py`
- `ChannelPointRedeems/custom_reward_example.py`

---

## Running the Bot

```bash
source .venv/bin/activate
python main.py
```

Expected startup behavior:

1. Connects to Twitch IRC
2. Starts the OBS browser refresh thread
3. Starts the background follower watcher
4. Begins writing chat messages to the overlay files

Typical startup log lines:

```text
[IRC] Connected to #yourchannel as yourbot
[Info] Follower watcher started (poll every 15s)
[OBS] Connected — OBS ..., WebSocket ...
[OBS] Refreshing 'Chat' every 0.5 second(s).
```

---

## Generated Files

The bot writes overlay-friendly files under `ExtraFiles/TextBasedFiles/`.

| File | Purpose |
|---|---|
| `ExtraFiles/TextBasedFiles/Chats/UnfilteredChat/chat.txt` | Raw chat log |
| `ExtraFiles/TextBasedFiles/Chats/UnfilteredChat/chat.html` | Raw styled HTML overlay |
| `ExtraFiles/TextBasedFiles/Chats/FilteredChat/chat.txt` | Filtered chat log |
| `ExtraFiles/TextBasedFiles/Chats/FilteredChat/chat.html` | Filtered styled HTML overlay |
| `ExtraFiles/TextBasedFiles/latest_follower.txt` | Latest follower name |
| `ExtraFiles/TextBasedFiles/latest_subscriber.txt` | Latest subscriber name |
| `ExtraFiles/TextBasedFiles/raid_info.txt` | Latest raid text |

Cache files are stored in `ExtraFiles/Cache/`.

---

## Channel Point Rewards

The reward system is wired through `ChannelPointRedeems/reward_command_combination.py`.

### To use a real reward:

1. Open `ChannelPointRedeems/reward_command_combination.py`
2. Replace the placeholder reward ID:

```py
EXAMPLE_CUSTOM_REWARD_ID = "replace-with-your-custom-reward-id"
```

3. Point that ID to a command function in `REWARD_COMMANDS`

The included example command in `ChannelPointRedeems/custom_reward_example.py` can:

- play a local sound file
- enable an OBS source briefly

> Note: the example sound file path must exist, or the command will log a warning and skip playback.

---

## Chat Filtering and Styling

### Filtered words

Edit `Chat/ChatFilters/filter_words.py` and `Chat/ChatFilters/filter.py` to customize blocked words.

### HTML chat styling

Edit `Chat/ChatMembers/chat_members.py`:

- `STYLE_RULES` controls conditional formatting
- `DEFAULT_STYLES` controls fallback styles

You can style users based on:

- moderator badges
- subscriber status
- Prime status
- follower time length

---

## Troubleshooting

### Bot connects to Twitch but no alerts appear in OBS

Check:

- OBS is open
- WebSocket is enabled on port `4455`
- `OBS_WEBSOCKET_PASSWORD` is correct
- scene and source names exactly match the constants in the code

### Chat files are not updating

Check:

- the bot is still running
- Twitch IRC connected successfully
- your overlay points at the files in `ExtraFiles/TextBasedFiles/Chats/`

### Follower data is missing

Check:

- `BROADCASTER_TOKEN` is valid
- `CLIENT_ID` is correct
- `USER_ID` in `ConfigFiles/channel_info.py` matches your channel

### Channel point rewards do nothing

Check:

- the real reward ID has replaced the placeholder in `reward_command_combination.py`
- the mapped function exists and is being called
- any sound files or OBS sources used by the reward command exist

---

## Security Notes

- Keep `ConfigFiles/tokens.py` **private**
- Do **not** commit tokens or secrets to Git
- If credentials were ever exposed, rotate them in the Twitch Developer Console and OBS

---

## Verification

The project was sanity-checked with:

```bash
/home/coby-brown/Documents/Programs/TwitchBot/.venv/bin/python -m py_compile $(find . -name '*.py' -not -path './.venv/*')
bash Setup/setup.sh
timeout 8s /home/coby-brown/Documents/Programs/TwitchBot/.venv/bin/python main.py
```

Verified behavior:

- Python files compile successfully
- setup script uses the repository-level `.venv`
- bot starts and connects to Twitch IRC
- OBS connection succeeds
- follower watcher starts
- routed cheer handling is active

---

## Next Customizations

Good first tweaks:

1. Replace the example reward ID with your real channel point reward ID
2. Add your own sound files / alert scenes
3. Tune the banned-word list and HTML chat styling
4. Adjust OBS source names to match your actual scene collection

Enjoy streaming. 🎥
