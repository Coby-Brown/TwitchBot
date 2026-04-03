from Chat import file_writer
from connect_twitch import connect


def main():
    # Connect once and let a single reader write all outputs.
    sock = connect()
    file_writer.write_messages(sock)


if __name__ == '__main__':
    main()