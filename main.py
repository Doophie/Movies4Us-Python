# main.py
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


movie_dir = open("movie_location.txt", "r").read().strip()

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


def build_connection_params(s):
    s.bind((ip, 0))
    s.listen(5)

    b64_key = base64.b64encode(secret_key).decode('utf-8')
    port = s.getsockname()[1]

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
    elif data == "playpause":
        pyautogui.press("playpause")
    elif data == "forward":
        pyautogui.press("right")
    elif data == "back":
        pyautogui.press("left")
    else:
        if sys.platform == "win32":
            os.startfile(movie_dir + "/" + data + '.mp4')
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, movie_dir + "/" + data + '.mp4'])


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        build_connection_params(s)

        while True:
            conn, addr = s.accept()

            thread.start_new_thread(connect_to_client, (conn, addr))
