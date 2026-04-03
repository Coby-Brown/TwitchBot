import socket
from ConfigFiles import tokens
from ConfigFiles import channel_info
import time


SERVER = 'irc.chat.twitch.tv'
PORT = 6667


def connect():
    oauth_token = tokens.TOKEN
    nickname = tokens.NICK
    channel = channel_info.CHANNEL

    sock = socket.socket()
    sock.connect((SERVER, PORT))
    sock.send(f"PASS {oauth_token}\r\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\r\n".encode('utf-8'))
    sock.send("CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership\r\n".encode('utf-8'))
    sock.send(f"JOIN #{channel}\r\n".encode('utf-8'))

    print(f"[IRC] Connected to #{channel} as {nickname}")
    message = f"{nickname} is here!"
    time.sleep(1)
    sock.send(f"PRIVMSG #{channel} :{message}\r\n".encode('utf-8'))
    return sock