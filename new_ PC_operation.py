import socket
import tkinter
from tkinter import Button
import numpy as np
import PIL.Image
import PIL.ImageTk
import cv2
import threading
import struct
from pyzbar.pyzbar import decode, ZBarSymbol

# デジタルズーム関数
def digital_zoom(frame, zoom_factor):
    height, width = frame.shape[:2]
    new_width = int(width / zoom_factor)
    new_height = int(height / zoom_factor)

    start_x = (width - new_width) // 2
    start_y = (height - new_height) // 2

    cropped_frame = frame[start_y:start_y +
                          new_height, start_x:start_x + new_width]
    zoomed_frame = cv2.resize(cropped_frame, (width, height))

    return zoomed_frame

# QRコードを取得する関数
def get_qr_text(frame: np.ndarray):
    value = decode(frame, symbols=[ZBarSymbol.QRCODE])
    return '\n'.join(list(map(lambda code: code.data.decode('utf-8'), value)))

# 各カメラのフレームを表示する関数
def update_image(data, canvas, photo_var, zoom_factor, zoom_lock):
    img = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(img, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # ズーム倍率をロックして取得
    with zoom_lock:
        zoomed_img = digital_zoom(img, zoom_factor[0])

    qr_text = get_qr_text(zoomed_img)
    if qr_text:
        print(f"QRコードが検出されました: {qr_text}")

    photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(zoomed_img))
    canvas.create_image(0, 0, image=photo, anchor=tkinter.NW)
    photo_var[0] = photo  # メモリ上で画像を保持するために参照を保存

# 各カメラの更新ループを実行する関数
def update_loop(client, canvas, photo_var, zoom_factor, zoom_lock):
    data = b""
    while True:
        try:
            while len(data) < 4:
                packet = client.recv(4096)
                if not packet:
                    return
                data += packet
            data_size = struct.unpack(">L", data[:4])[0]
            data = data[4:]

            while len(data) < data_size:
                packet = client.recv(4096)
                if not packet:
                    return
                data += packet

            img_data = data[:data_size]
            data = data[data_size:]
            update_image(img_data, canvas, photo_var, zoom_factor, zoom_lock)
        except Exception as e:
            print(f"Error in update_loop: {e}")
            break

# カメラの切り替え関数
def switch_camera(current_camera_var, canvas1, canvas2):
    if current_camera_var[0] == 1:
        current_camera_var[0] = 2
        canvas1.pack_forget()  # 現在のカメラを隠す
        canvas2.pack(side="left")  # 2番目のカメラを表示
        print("Switched to Camera 2")
    else:
        current_camera_var[0] = 1
        canvas2.pack_forget()  # 現在のカメラを隠す
        canvas1.pack(side="left")  # 1番目のカメラを表示
        print("Switched to Camera 1")

def on_key_press(event, zoom_factor, zoom_lock, current_camera_var, canvas1, canvas2):
    if event.keysym == 'q':
        window.quit()
    elif event.char.isdigit():  # 数字キーが押された場合
        with zoom_lock:  # ズーム倍率をロックして更新
            zoom_factor[0] = int(event.char)
        print(f"Zoom set to: {zoom_factor[0]}")
    elif event.keysym == 'c':  # 'c'キーでカメラを切り替える
        switch_camera(current_camera_var, canvas1, canvas2)

# メインウィンドウの作成
window = tkinter.Tk()
window.title("カメラ映像表示")

# 2つのキャンバスを作成（それぞれのカメラ用）
canvas1 = tkinter.Canvas(window, width=640, height=480)
canvas1.pack(side="left")

canvas2 = tkinter.Canvas(window, width=640, height=480)
canvas2.pack_forget()  # 初期状態では2番目のカメラを非表示にする

# 画像参照を保持する変数を作成（それぞれのカメラ用）
photo_var1 = [None]
photo_var2 = [None]

# ズーム倍率を保持する変数とロック
zoom_factor = [1]  # リストでズーム倍率を保持
zoom_lock = threading.Lock()

# 現在表示しているカメラを保持する変数
current_camera_var = [1]  # 初期状態ではカメラ1

SERVER_IP = "172.20.10.2"  # ★ラズパイのIPアドレスを指定してください
SERVER_PORT = 36131        # ★ラズパイのサーバーポートを指定してください

# ソケット接続の確立
client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client1.connect((SERVER_IP, SERVER_PORT))

client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client2.connect((SERVER_IP, SERVER_PORT))

# qキーでプログラムを終了するためのイベントバインド
window.bind('<KeyPress>', lambda event: on_key_press(
    event, zoom_factor, zoom_lock, current_camera_var, canvas1, canvas2))

# フレームの更新ループを実行するスレッドを開始（それぞれのカメラ用）
thread1 = threading.Thread(target=update_loop, args=(
    client1, canvas1, photo_var1, zoom_factor, zoom_lock))
thread2 = threading.Thread(target=update_loop, args=(
    client2, canvas2, photo_var2, zoom_factor, zoom_lock))

thread1.daemon = True
thread2.daemon = True
thread1.start()
thread2.start()

# メインのTkinterイベントループを開始
window.mainloop()
