import socket
import tkinter
from tkinter import Button
import threading
import pygame
import controller_get as con
import copy
from camera_manager import CameraManager
from concurrent.futures import ThreadPoolExecutor

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


def switch_camera(event, current_camera_var, canvas_list):
    """カメラの表示モードを切り替える"""
    if event.keysym == 'a':  # 全カメラ表示モード
        current_camera_var = 0  # 0は「全カメラ表示」
        for canvas in canvas_list:
            canvas.pack(side="left")  # すべてのカメラを表示
        print("Switched to All Camera Mode")

    elif event.keysym in ['1', '2']:  # 個別カメラ表示モード
        current_camera_var = int(event.keysym)  # 押されたキー（1, 2）に対応
        for i, canvas in enumerate(canvas_list):
            if i + 1 == current_camera_var:  # 選ばれたカメラのみ表示
                canvas.pack(side="left", expand=True, fill="both")
            else:
                canvas.pack_forget()
        print(f"Switched to Camera {current_camera_var} Mode")

    return current_camera_var  # 変更後のカメラ状態を返す

def on_key_press(event, zoom_factor, zoom_lock, current_camera_var, canvas_list, window):
    """キー入力を処理し、カメラの表示切り替えやズームを行う"""
    if event.keysym == 'q':
        window.quit()

    elif event.keysym in ['1', '2', 'a']:
        current_camera_var = switch_camera(
            event, current_camera_var, canvas_list)

    elif event.keysym == 'plus':  # ズームイン
        with zoom_lock:
            zoom_factor[0] = min(zoom_factor[0] + 1, 5)  # 最大5倍まで
        print(f"Zoom In: {zoom_factor[0]}x")

    elif event.keysym == 'minus':  # ズームアウト
        with zoom_lock:
            zoom_factor[0] = max(zoom_factor[0] - 1, 1)  # 最小1倍まで
        print(f"Zoom Out: {zoom_factor[0]}x")

def controller_loop():
  # ジョイスティックの初期化
  pygame.init()
  j = pygame.joystick.Joystick(0)
  j.init()

  SERVER_PORT_CONTROLLER = 36132        # ★ラズパイのサーバーポートを指定してください
  port = 36133               # ★コントローラーのサーバーポートを指定してください
  
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
  sv.settimeout(0.1)  # **ソケットをノンブロッキングに**

  with ThreadPoolExecutor(max_workers=4) as executor:  # **並列送信**

  # **Tkinterのイベントループとコントローラー入力の送信を並行実行**
    while True:
      try:
            try:
                    client, addr = sv.accept()
            except socket.timeout:
                    client = None

            if client:
                    print(f"接続受理: {addr}")

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

      except Exception as e:
        print(f"Error: {e}")


def main():
  # メインウィンドウの作成
  window = tkinter.Tk()
  window.title("カメラ映像表示")

  # 2つのキャンバスを作成（それぞれのカメラ用）
  canvas1 = tkinter.Canvas(window, width=640, height=480)
  canvas1.pack(side="left")

  canvas2 = tkinter.Canvas(window, width=640, height=480)
  canvas2.place_forget()  # 初期状態では2番目のカメラを非表示にする

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

  # ソケット接続の確立
  client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client1.connect((SERVER_IP, SERVER_PORT))

  client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client2.connect((SERVER_IP, SERVER_PORT))

  # qキーでプログラムを終了するためのイベントバインド
  window.bind('<KeyPress>', lambda event: on_key_press(
      event, zoom_factor, zoom_lock, current_camera_var, canvas_list, window))

  camera1 = CameraManager(SERVER_IP, SERVER_PORT, canvas1,window)
  camera2 = CameraManager(SERVER_IP, SERVER_PORT, canvas2,window)


  # **スレッドプールの作成**
  with ThreadPoolExecutor(max_workers=7) as executor:
      # カメラデータ受信スレッド
      executor.submit(camera1.update_loop, client1, canvas1,photo_var1,zoom_factor, zoom_lock)
      executor.submit(camera2.update_loop, client2, canvas2,photo_var2,zoom_factor, zoom_lock)

      # コントローラーの入力処理
      executor.submit(controller_loop)

      # **Tkinterのメインループを実行**
      window.mainloop()
  
# スクリプトとして実行された場合に main() を呼び出す
if __name__ == "__main__":
    main()
