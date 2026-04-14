import socket
from ConfigFiles import tokens
from ConfigFiles import channel_info
import time


SERVER = 'irc.chat.twitch.tv'
PORT = 6667
HANDSHAKE_TIMEOUT_SECONDS = 15


def _raise_on_auth_error(line: str) -> None:
    lowered = line.lower()
    if 'login authentication failed' in lowered or 'improperly formatted auth' in lowered:
        raise ConnectionError(
            'Twitch IRC authentication failed. Update ConfigFiles/tokens.py TOKEN '
            'with a valid oauth token that includes chat:read and chat:edit scopes.'
        )


def _wait_for_handshake(sock: socket.socket) -> None:
    deadline = time.time() + HANDSHAKE_TIMEOUT_SECONDS
    buffer = ''

    while time.time() < deadline:
        try:
            payload = sock.recv(2048).decode('utf-8', errors='ignore')
        except socket.timeout:
            continue

        if not payload:
            raise ConnectionError('Twitch IRC closed connection during login handshake.')

        buffer += payload
        lines = buffer.split('\r\n')
        buffer = lines.pop() if lines else ''

        for line in lines:
            if not line:
                continue
            if line.startswith('PING'):
                sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
                continue

            _raise_on_auth_error(line)

            if ' 001 ' in line or ' GLOBALUSERSTATE ' in line:
                return

    raise ConnectionError('Timed out waiting for Twitch IRC login confirmation.')


def connect():
    oauth_token = tokens.TOKEN
    nickname = tokens.NICK
    channel = channel_info.CHANNEL

    sock = socket.socket()
    sock.settimeout(HANDSHAKE_TIMEOUT_SECONDS)
    sock.connect((SERVER, PORT))
    sock.send(f"PASS {oauth_token}\r\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
    sock.send("CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership\r\n".encode('utf-8'))
    sock.send(f"JOIN #{channel}\r\n".encode('utf-8'))

    _wait_for_handshake(sock)
    sock.settimeout(None)

    print(f"[IRC] Connected to #{channel} as {nickname}")
    message = f"{nickname} is here!"
    time.sleep(1)
    sock.send(f"PRIVMSG #{channel} :{message}\r\n".encode('utf-8'))
    return sock