from Chat import file_writer
from chat_refresh import start_refresh_thread
from connect_twitch import connect as connect_twitch


def main():
    # Connect once, start OBS browser refreshing, and let a single reader write all outputs.
    sock = connect_twitch()
    start_refresh_thread()
    file_writer.write_messages(sock)


if __name__ == '__main__':
    main()