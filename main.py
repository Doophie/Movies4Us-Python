# main.py
import json
import os
import socket
import subprocess
import sys

import qrcode
import base64
import pyautogui
import _thread as thread
from PIL import Image
from os.path import isfile, join
from os import listdir


movie_dir = "/Volumes/Triactor/Movies"
connection_param_file = "connection_params.json"

secret_key = bytearray(os.urandom(32))


def get_movie_list():
    filenames = [f for f in listdir(movie_dir) if isfile(join(movie_dir, f))]

    return ";".join([f.split(".")[0] for f in filenames]) + ";"


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


ip = get_local_ip()


def build_connection_params(s, c_port=0, c_key=None):
    s.bind((ip, c_port))
    s.listen(5)

    if c_key is not None:
        b64_key = c_key
    else:
        b64_key = base64.b64encode(secret_key).decode('utf-8')

    port = s.getsockname()[1]

    with open(connection_param_file, 'w') as f:
        json.dump({"port":port, "key":b64_key}, f)


    qrcode.make(f"{ip}&{port}&{b64_key}").save("qr_code.jpg")

    Image.open("qr_code.jpg").show()


def connect_to_client(conn, addr):
    with conn:
        print(f"Connect to {addr}")

        conn.send("ack".encode("utf-8"))

        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
            except Exception:
                print("connection closed")
                break

            if len(data) <= 0:
                continue

            if data == "ping-test":
                print(f"Got ping test from {addr}")
                conn.send("ack".encode("utf-8"))
                continue

            # result_string = aes_cipher.AESCipher(secret_key).decrypt(data)
            print(f"Got data {data}")#result_string}")

            parse_data(conn, data)
            print("Writing bytes")
            # conn.send("ack".encode("utf-8"))


def parse_data(conn, data):
    if data == "get_movie_list":
        #print("sending this movirew")
        conn.send(get_movie_list().encode("utf-8"))
    if data == "playpause":
        pyautogui.press("playpause")
    if data == "forward":
        pyautogui.press("right")
    if data == "back":
        pyautogui.press("left")
    else:
        if sys.platform == "win32":
            os.startfile(movie_dir + "/" + data + '.mp4')
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, movie_dir + "/" + data + '.mp4'])

# Returns None if they dont exist
def get_connection_params():
    if os.path.isfile(connection_param_file):
        with open(connection_param_file, "r") as jsonfile:
            return json.load(jsonfile)
    else:
        return None

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        cp = get_connection_params()
        if cp is not None:
            build_connection_params(s, cp["port"], cp["key"])
        else:
            build_connection_params(s)

        while True:
            conn, addr = s.accept()

            thread.start_new_thread(connect_to_client, (conn, addr))
