import socket
import tkinter
from tkinter import Button
import threading
import pygame
import controller_get as con
import copy
from camera_manager import CameraManager

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

def switch_camera(event, current_camera_var, canvas_list, zoom_factor, zoom_lock):
    """カメラの表示モードを切り替える + ズーム機能の調整"""

    if event.keysym == 'a':  # 全カメラ表示モード
        current_camera_var[0] = 0  # 0は「全カメラ表示」
        for canvas in canvas_list:
            canvas.pack(side="left")  # すべてのカメラを表示
        print("Switched to All Camera Mode")

    elif event.keysym in ['1', '2']:  # 個別カメラ表示モード
        current_camera_var[0] = int(event.keysym)  # 1, 2, 3 のどれが押されたか取得
        for i, canvas in enumerate(canvas_list):
            if i + 1 == current_camera_var[0]:  # 選ばれたカメラだけ表示
                canvas.pack(side="left", expand=True, fill="both")
            else:
                canvas.pack_forget()
        print(f"Switched to Camera {current_camera_var[0]} Mode")

    elif event.keysym == 'plus':  # ズームイン（+キー）
        with zoom_lock:
            zoom_factor[0] = min(zoom_factor[0] + 1, 5)  # 最大5倍まで
        print(f"Zoom In: {zoom_factor[0]}x")

    elif event.keysym == 'minus':  # ズームアウト（-キー）
        with zoom_lock:
            zoom_factor[0] = max(zoom_factor[0] - 1, 1)  # 最小1倍まで
        print(f"Zoom Out: {zoom_factor[0]}x")

def on_key_press(event, zoom_factor, zoom_lock, current_camera_var, canvas_list, window):
    if event.keysym == 'q':
        window.quit()
    elif event.keysym in ['1', '2', '3', 'a', 'plus', 'minus']:
        switch_camera(event, current_camera_var,
                      canvas_list, zoom_factor, zoom_lock)

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

  # キャンバスリストを作成
  canvas_list = [canvas1, canvas2]

  # ズーム倍率を保持する変数とロック
  zoom_factor = [1]  # リストでズーム倍率を保持
  zoom_lock = threading.Lock()

  # 現在表示しているカメラを保持する変数
  current_camera_var = [0]  # 初期状態ではカメラ1

  SERVER_IP = "10.133.7.48"  # ★ラズパイのIPアドレスを指定してください
  SERVER_PORT = 36131        # ★ラズパイのサーバーポートを指定してください
  SERVER_PORT_CONTROLLER = 36132        # ★ラズパイのサーバーポートを指定してください
  port = 36133               # ★コントローラーのサーバーポートを指定してください

  # ソケット接続の確立
  client0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client0.connect((SERVER_IP, SERVER_PORT))

  client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client1.connect((SERVER_IP, SERVER_PORT))

  # qキーでプログラムを終了するためのイベントバインド
  window.bind('<KeyPress>', lambda event: on_key_press(
      event, zoom_factor, zoom_lock, current_camera_var, canvas_list, window))

  # キーボード入力のバインド
  window.bind('<KeyPress>', lambda event: switch_camera(
      event, current_camera_var, canvas_list,zoom_factor, zoom_lock))

  camera1 = CameraManager(SERVER_IP, SERVER_PORT, canvas1)
  camera2 = CameraManager(SERVER_IP, SERVER_PORT, canvas2)

  # フレームの更新ループを実行するスレッドを開始（それぞれのカメラ用）
  thread0 = threading.Thread(target=camera1.update_loop, args=(
      client0, canvas1, photo_var1, zoom_factor, zoom_lock))
  thread1 = threading.Thread(target=camera2.update_loop, args=(
      client1, canvas2, photo_var2, zoom_factor, zoom_lock))

  thread0.daemon = True
  thread1.daemon = True

  thread0.start()
  print("スレッド開始: カメラ1")
  thread1.start()
  print("スレッド開始: カメラ2")

  # コントローラーの更新ループを実行するスレッドを開始
  hat_data = [0] * 2
  botan_data = [0] * 10
  Lstick_data = [0] * 2
  Rstick_data = [0] * 2
  hat_data_old = [0] * 2
  botan_data_old = [0] * 10
  Lstick_data_old = [0] * 2
  Rstick_data_old = [0] * 2

  sv = socket.socket(socket.AF_INET)
  sv.bind((socket.gethostbyname(socket.gethostname()), SERVER_PORT_CONTROLLER))
  sv.listen()

 # **Tkinterのイベントループとコントローラー入力の送信を並行実行**
  while True:
    # Tkinterのウィンドウを更新
    window.update_idletasks()
    window.update()

    # コントローラー入力の取得
    Rstick_data = copy.deepcopy(con.getstick(3, 2, sv, port, j))
    Lstick_data = copy.deepcopy(con.getstick(0, 1, sv, port, j))
    hat_data = copy.deepcopy(con.gethat(sv, port, j))
    events = pygame.event.get()
    for event in events:
      if event.type == pygame.JOYBUTTONDOWN:  # ボタンが押された場合
        botan_data = copy.deepcopy(con.getbotan(sv, port, j))
      if event.type == pygame.JOYBUTTONUP:  # ボタンが押された場合
        botan_data = copy.deepcopy(con.getbotan(sv, port, j))
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


# スクリプトとして実行された場合に main() を呼び出す
if __name__ == "__main__":
    main()
