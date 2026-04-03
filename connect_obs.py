import obsws_python as obs
from ConfigFiles import tokens


HOST = 'localhost'
PORT = 4455


def connect():
    password = tokens.OBS_WEBSOCKET_PASSWORD

    client = obs.ReqClient(host=HOST, port=PORT, password=password)
    version = client.get_version()
    print(f"[OBS] Connected — OBS {version.obs_version}, WebSocket {version.obs_web_socket_version}")
    return client
