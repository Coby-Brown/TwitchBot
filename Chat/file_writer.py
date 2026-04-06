from Chat.ChatFilters import filter
from Chat.ChatMembers import chat_members
from Chat.ChatMembers import chat_lookup
import socket
import time


UNFILTERED_TXT_PATH = 'Chat/UnfilteredChat/chat.txt'
UNFILTERED_HTML_PATH = 'Chat/UnfilteredChat/chat.html'
FILTERED_TXT_PATH = 'Chat/FilteredChat/chat.txt'
FILTERED_HTML_PATH = 'Chat/FilteredChat/chat.html'
HTML_RETENTION_SECONDS = 30


def _render_recent_html(html_file, html_window, now_epoch):
    cutoff = now_epoch - HTML_RETENTION_SECONDS
    html_window[:] = [row for row in html_window if row[0] >= cutoff]

    html_file.seek(0)
    html_file.truncate()
    for _, html_line in html_window:
        html_file.write(html_line + '\n')
    html_file.flush()


def _prune_html_windows(unfiltered_html, filtered_html, unfiltered_html_window, filtered_html_window):
    now_epoch = int(time.time())
    _render_recent_html(unfiltered_html, unfiltered_html_window, now_epoch)
    _render_recent_html(filtered_html, filtered_html_window, now_epoch)

def _extract_message(line):
    parsed = _parse_privmsg_line(line)
    if not parsed:
        return None
    message = parsed['message'].strip()
    return message or None


def _extract_username_from_line(line):
    parsed = _parse_privmsg_line(line)
    if not parsed:
        return 'unknown'
    return parsed['username']


def _parse_privmsg_line(line):
    raw = line.strip()

    # Strip IRC tags first (for lines starting with @badge-info=...)
    if raw.startswith('@'):
        _, _, raw = raw.partition(' ')

    if not raw.startswith(':'):
        return None

    source, sep, command_payload = raw[1:].partition(' PRIVMSG ')
    if not sep:
        return None

    _, message_sep, message = command_payload.partition(' :')
    if not message_sep:
        return None

    username = source.split('!', 1)[0] if '!' in source else source
    return {
        'username': username or 'unknown',
        'message': message,
    }


def _write_message(
    member_info,
    username,
    message,
    unfiltered_txt,
    unfiltered_html,
    filtered_txt,
    filtered_html,
    unfiltered_html_window,
    filtered_html_window,
):
    now_epoch = int(time.time())
    line = f"{username}: {message}"

    unfiltered_txt.write(line + '\n')
    unfiltered_txt.flush()

    unfiltered_html_line = chat_members.build_html_line(username, message, member_info)
    unfiltered_html_window.append((now_epoch, unfiltered_html_line))
    _render_recent_html(unfiltered_html, unfiltered_html_window, now_epoch)

    filtered_message = filter.filter_message(message)
    if filtered_message:
        filtered_line = f"{username}: {filtered_message}"

        filtered_txt.write(filtered_line + '\n')
        filtered_txt.flush()

        filtered_html_line = chat_members.build_html_line(username, filtered_message, member_info)
        filtered_html_window.append((now_epoch, filtered_html_line))
        _render_recent_html(filtered_html, filtered_html_window, now_epoch)


def write_messages(sock, reward_handler=None):
    unfiltered_html_window = []
    filtered_html_window = []
    sock.settimeout(1.0)

    with open(UNFILTERED_TXT_PATH, 'a', encoding='utf-8') as unfiltered_txt, \
         open(UNFILTERED_HTML_PATH, 'w+', encoding='utf-8') as unfiltered_html, \
         open(FILTERED_TXT_PATH, 'a', encoding='utf-8') as filtered_txt, \
         open(FILTERED_HTML_PATH, 'w+', encoding='utf-8') as filtered_html:
        while True:
            try:
                response = sock.recv(2048).decode('utf-8', errors='ignore')
            except socket.timeout:
                _prune_html_windows(unfiltered_html, filtered_html, unfiltered_html_window, filtered_html_window)
                continue

            for line in response.splitlines():
                if line.startswith('PING'):
                    sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                    continue

                if reward_handler is not None:
                    try:
                        reward_handler(line)
                    except Exception as exc:
                        print(f"[Reward] Handler error: {exc}")

                message = _extract_message(line)
                if message:
                    member_info = chat_lookup.lookup_member_info(line)
                    username = member_info.get('username') or _extract_username_from_line(line)
                    _write_message(
                        member_info,
                        username,
                        message,
                        unfiltered_txt,
                        unfiltered_html,
                        filtered_txt,
                        filtered_html,
                        unfiltered_html_window,
                        filtered_html_window,
                    )

            _prune_html_windows(unfiltered_html, filtered_html, unfiltered_html_window, filtered_html_window)