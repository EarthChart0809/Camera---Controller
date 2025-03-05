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
import pygame
import controller_get as con
import copy

NUMBEROFBOTTONS = 10
NUMBEROFSTICKS = 6
STICK_PLAY = -10
STICK_VAULE = 250
hat_value = [0, 0]
sendstick = [0, 0]
botan_value = [0] * NUMBEROFBOTTONS
X = 0
Y = 1
A = 2
B = 3
LB = 4
RB = 5
LS = 8
RS = 9
LT = 6
RT = 7
L = 0
R = 1
H = 2
BOTAN = 3
VARTICAL = 0
WIDTH = 1
HAT_NUMBER = 0

def portcheck(bunsho):
  while True:
    try:
      p = int(input(bunsho))
    except ValueError:
      print("入力できていません")
      continue
    return p

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
    print("カメラの受信ループ開始")
    while True:
        try:
            while len(data) < 4:
                packet = client.recv(4096)
                if not packet:
                    return
                data += packet
            data_size = struct.unpack(">L", data[:4])[0]
            data = data[4:]

            print(f"受信データサイズ: {data_size} バイト")

            while len(data) < data_size:
                packet = client.recv(4096)
                if not packet:
                    return
                data += packet

            img_data = data[:data_size]
            data = data[data_size:]
            print(f"画像データを受信: {len(img_data)} バイト")
            update_image(img_data, canvas, photo_var, zoom_factor, zoom_lock)
        except Exception as e:
            print(f"Error in update_loop: {e}")
            break

def controller_loop(sv,port,j,SERVER_IP,SERVER_PORT_CONTROLLER):
  SERVER_IP = "10.133.7.48"  # ★ラズパイのIPアドレスを指定してください
  SERVER_PORT_CONTROLLER = 36132        # ★ラズパイのサーバーポートを指定してください
  client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client2.connect((SERVER_IP, SERVER_PORT_CONTROLLER))

  hat_data = [0] * 2
  botan_data = [0] * 10
  Lstick_data = [0] * 2
  Rstick_data = [0] * 2
  hat_data_old = [0] * 2
  botan_data_old = [0] * 10
  Lstick_data_old = [0] * 2
  Rstick_data_old = [0] * 2

  print("コントローラーループ開始")


  # コールバック要求クライアント
  while True:
    Rstick_data = copy.deepcopy(con.getstick(3, 2, sv, port, j))
    Lstick_data = copy.deepcopy(con.getstick(0, 1, sv, port, j))
    hat_data = copy.deepcopy(con.gethat(sv, port, j))
    events = pygame.event.get()
    for event in events:
      if event.type == pygame.JOYBUTTONDOWN:  # ボタンが押された場合
        botan_data = copy.deepcopy(con.getbotan(sv, port, j))
      if event.type == pygame.JOYBUTTONUP:  # ボタンが押された場合
        botan_data = copy.deepcopy(con.getbotan(sv, port, j))

    # **デバッグ用のログ**
        print(
            f"取得データ: hat={hat_data}, Lstick={Lstick_data}, Rstick={Rstick_data}, buttons={botan_data}")

    if not hat_data == hat_data_old:
      con.contorollerdata_send(hat_data[WIDTH], VARTICAL, H, sv, port)
      con.contorollerdata_send(hat_data[VARTICAL], VARTICAL, H, sv, port)
      hat_data_old = copy.deepcopy(hat_data)
    if not Lstick_data == Lstick_data_old:
      con.contorollerdata_send(Lstick_data[WIDTH], WIDTH, L, sv, port)
      con.contorollerdata_send(Lstick_data[VARTICAL], VARTICAL, L, sv, port)
      Lstick_data_old = copy.deepcopy(Lstick_data)
    if not Rstick_data == Rstick_data_old:
      con.contorollerdata_send(Rstick_data[WIDTH], WIDTH, R, sv, port)
      con.contorollerdata_send(
          cmd=Rstick_data[VARTICAL], sendc=VARTICAL, kind=R, sv=sv, port=port)
      Rstick_data_old = copy.deepcopy(Rstick_data)
    for i in range(NUMBEROFBOTTONS):
      if not botan_data[i] == botan_data_old[i]:
        con.contorollerdata_send(botan_data[i], i, BOTAN, sv, port)
        botan_data_old = copy.deepcopy(botan_data)

def switch_camera(current_camera_var, canvas1, canvas2):
    if current_camera_var[0] == 1:
        current_camera_var[0] = 2
        canvas2.lift()  # 2番目のカメラを前面に表示
        print("Switched to Camera 2")
    else:
        current_camera_var[0] = 1
        canvas1.lift()  # 1番目のカメラを前面に表示
        print("Switched to Camera 1")

def on_key_press(event, zoom_factor, zoom_lock, current_camera_var, canvas1, canvas2, window):
    if event.keysym == 'q':
        window.quit()
    elif event.char.isdigit():  # 数字キーが押された場合
        with zoom_lock:  # ズーム倍率をロックして更新
            zoom_factor[0] = int(event.char)
        print(f"Zoom set to: {zoom_factor[0]}")
    elif event.keysym == 'c':  # 'c'キーでカメラを切り替える
        switch_camera(current_camera_var, canvas1, canvas2)

def main():
  # メインウィンドウの作成
  window = tkinter.Tk()
  window.title("カメラ映像表示")

  # 2つのキャンバスを作成（それぞれのカメラ用）
  canvas1 = tkinter.Canvas(window, width=640, height=480)
  canvas1.pack(side="left")

  canvas2 = tkinter.Canvas(window, width=640, height=480)
  canvas2.pack_forget()  # 初期状態では2番目のカメラを非表示にする

  # ジョイスティックの初期化
  pygame.init()
  j = pygame.joystick.Joystick(0)
  j.init()

  # 画像参照を保持する変数を作成（それぞれのカメラ用）
  photo_var1 = [None]
  photo_var2 = [None]

  # ズーム倍率を保持する変数とロック
  zoom_factor = [1]  # リストでズーム倍率を保持
  zoom_lock = threading.Lock()

  # 現在表示しているカメラを保持する変数
  current_camera_var = [1]  # 初期状態ではカメラ1

  SERVER_IP = "10.133.7.48"  # ★ラズパイのIPアドレスを指定してください
  SERVER_PORT = 36131        # ★ラズパイのサーバーポートを指定してください
  SERVER_PORT_CONTROLLER = 36132        # ★ラズパイのサーバーポートを指定してください
  
  # ソケット接続の確立
  client0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client0.connect((SERVER_IP, SERVER_PORT))

  client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client1.connect((SERVER_IP, SERVER_PORT))

  # qキーでプログラムを終了するためのイベントバインド
  window.bind('<KeyPress>', lambda event: on_key_press(
      event, zoom_factor, zoom_lock, current_camera_var, canvas1, canvas2, window))

  # フレームの更新ループを実行するスレッドを開始（それぞれのカメラ用）
  thread0 = threading.Thread(target=update_loop, args=(
      client0, canvas1, photo_var1, zoom_factor, zoom_lock))
  thread1 = threading.Thread(target=update_loop, args=(
      client1, canvas2, photo_var2, zoom_factor, zoom_lock))

  # コントローラーの更新ループを実行するスレッドを開始
  controller_thread = threading.Thread(target=controller_loop,args=(j,SERVER_IP,SERVER_PORT_CONTROLLER))

  thread0.daemon = True
  thread1.daemon = True
  controller_thread.daemon = True
  print("スレッド開始: カメラ1")
  thread0.start()
  print("スレッド開始: カメラ2")
  thread1.start()
  print("スレッド開始: コントローラー")
  controller_thread.start()

  # メインのTkinterイベントループを開始
  window.mainloop()

# スクリプトとして実行された場合に main() を呼び出す
if __name__ == "__main__":
    main()
