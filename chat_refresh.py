import argparse
import threading
import time

from connect_obs import connect


DEFAULT_SOURCE_NAME = 'Chat'
DEFAULT_INTERVAL = 0.5
DEFAULT_PROPERTY = 'refreshnocache'


def refresh_browser_source(
    source_name=DEFAULT_SOURCE_NAME,
    interval=DEFAULT_INTERVAL,
    prop_name=DEFAULT_PROPERTY,
    client=None,
):
    owns_client = client is None
    if owns_client:
        client = connect()

    print(f"[OBS] Refreshing '{source_name}' every {interval:.1f} second(s).")

    try:
        while True:
            client.press_input_properties_button(source_name, prop_name)
            time.sleep(interval)
    except Exception as exc:
        print(f"[OBS] Auto refresh error for '{source_name}': {exc}")
    finally:
        if owns_client and client is not None:
            client.disconnect()


def start_refresh_thread(source_name=DEFAULT_SOURCE_NAME, interval=DEFAULT_INTERVAL, prop_name=DEFAULT_PROPERTY):
    refresh_thread = threading.Thread(
        target=refresh_browser_source,
        args=(source_name, interval, prop_name),
        daemon=True,
        name='obs-browser-refresh',
    )
    refresh_thread.start()
    return refresh_thread


def main():
    parser = argparse.ArgumentParser(
        description='Automatically refresh an OBS browser source on a timer.'
    )
    parser.add_argument(
        'source_name',
        nargs='?',
        default=DEFAULT_SOURCE_NAME,
        help='Exact name of the OBS browser source to refresh. Default: Chat',
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=DEFAULT_INTERVAL,
        help='Seconds between refreshes. Default: 0.5',
    )
    parser.add_argument(
        '--property',
        dest='prop_name',
        default=DEFAULT_PROPERTY,
        help='OBS browser source property button to press. Default: refreshnocache',
    )

    args = parser.parse_args()

    if args.interval <= 0:
        parser.error('--interval must be greater than 0.')

    refresh_browser_source(args.source_name, interval=args.interval, prop_name=args.prop_name)


if __name__ == '__main__':
    main()
