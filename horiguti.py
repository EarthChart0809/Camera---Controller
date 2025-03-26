import queue
import socket
import cv2
import numpy as np
import serial
import struct
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future

SERVER_IP = '10.133.7.48'
SERVER_PORT = 36131
SERVER_PORT_CONTROLLER = 36132
SERVER_PORT_SERIAL = 36133
BUFSIZE = 4096
data_get: list[Future] = [0] * 4   # 型をFutureに変更
data_return = []

# シリアルポートの初期化
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
ser.flush()

z = 0
serialsetting = {"communicationpartner": '/dev/ttyACM0',
                 "baudrate": 115200, "timeout_second": 1}


class conection:
  def __init__(self):
    self.data_get = [] * 4
    self.data_return = []
    self.ser = serial.Serial(
        serialsetting["communicationpartner"], serialsetting["baudrate"], timeout=serialsetting["timeout_second"])
    self.sv = socket.socket(socket.AF_INET)
    self.socketsetting = {"sendport": 0,
                          "replyport": 0, "ip": "192.168.246.106"}
    self.socketsetting["sendport"] = int(input("port番号を打ち込んでください"))
    self.socketsetting["replyport"] = int(input("port番号を打ち込んでください"))
    self.contime = []

  def serialtusin(self):
    msg = str(self.data_return[-1]) + "\n"
    self.ser.write(msg.encode('utf-8'))
    while self.ser.in_waiting > 0:
      print("A")
    line = self.ser.readline().decode('utf-8').rstrip()
    print(line)
    time.sleep(0.01)

  def tunagu(self):
    client, addr = self.sv.accept()
    return client

  def backlog(self):
    with ThreadPoolExecutor(max_workers=4) as executor:
      setuzoku = executor.submit(tunagu)
      while (True):
        self.serialtusin()
        self.data_return.pop(-1)
        time.sleep(self.contime[-1])
        self.contime.pop(-1)
        try:
          client = setuzoku.result(timeout=1)
          client.close()
          break
        except TimeoutError:
          continue
        except:
          print("なんかエラー")

  def responseToCommand(self, client, addr):
    start = time.time()
    # 処理：コンソールにエコーする
    data = client.recv(1024)
    comand = data.decode("utf-8")
    # クライアントに返答
    res = socket.socket(socket.AF_INET)
    res.connect((addr[0], self.socketsetting[replyport]))
    res.send("Thank you!".encode("utf-8"))
    client.close()
    res.close()
    print(comand)
    end = time.time()
    return comand, end - start


# キューを作成（エンコード待ちの画像フレームを格納）
frame_queue = queue.Queue(maxsize=5)  # キューのサイズを適切に設定

def encode_and_send(client_socket, frame_queue):
  """画像をエンコードして送信（別スレッドで処理）"""
  while True:
    try:
      frame = frame_queue.get()  # キューからフレームを取得
      if frame is None:
        break  # Noneを受け取ったらスレッド終了

      # **JPEG にエンコード（圧縮率を調整）**
      encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),
                      50]  # 画質 50 に設定（40 から微調整）
      _, img_encoded = cv2.imencode('.jpg', frame, encode_param)
      data = img_encoded.tobytes()

      # **フレームサイズを送信**
      data_size = struct.pack(">L", len(data))
      client_socket.sendall(data_size)
      client_socket.sendall(data)

    except Exception as e:
      print(f"Error in encode_and_send: {e}")
      break

def capture_camera(camera_index, frame_queue, client_socket):
  """カメラキャプチャ（メインスレッドで処理）"""
  cap = cv2.VideoCapture(camera_index)
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # 解像度を下げて軽量化
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
  cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # バッファを小さくして遅延を減らす
  cap.set(cv2.CAP_PROP_FPS, 15)  # FPSを下げてCPU負荷を軽減

  # # **TCP通信の最適化**
  # client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 即時送信
  # client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)  # 送信バッファサイズを小さく
  # client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)  # 受信バッファサイズを小さく
  # client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # KeepAliveを有効化

  if not cap.isOpened():
    print(f"Error: Could not open camera {camera_index}.")
    return

  try:
    while True:
      ret, frame = cap.read()
      if not ret:
        print(
            f"Error: Failed to capture image from camera {camera_index}.")
        time.sleep(0.05)
        continue

      # **フレームをキューに追加（エンコードスレッドが処理）**
      if not frame_queue.full():  # キューが満杯ならスキップして最新フレームを優先
        frame_queue.put(frame)

  except Exception as e:
    print(f"Error in capture_camera {camera_index}: {e}")
  finally:
    cap.release()
    frame_queue.put(None)  # エンコードスレッドを終了させる


def main():

  # メイン処理
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((SERVER_IP, SERVER_PORT))
  server.listen(2)  # 2つのクライアントを待機

  print("Waiting for connection...")

  sv = socket.socket(socket.AF_INET)
  sv.bind((SERVER_IP, SERVER_PORT_SERIAL))
  sv.listen()
  sv.settimeout(1.0)  # **タイムアウトを 1 秒に**

  print(f"コントローラーデータ受信中... ポート: {SERVER_PORT_SERIAL}")

  client_socket1, client_address1 = server.accept()
  print(f"Connection from: {client_address1} for Camera 1")

  client_socket2, client_address2 = server.accept()
  print(f"Connection from: {client_address2} for Camera 2")

  # **カメラごとのフレームキューを作成**
  frame_queue1 = queue.Queue(maxsize=5)
  frame_queue2 = queue.Queue(maxsize=5)

  # **エンコード専用スレッドを開始**
  encode_thread1 = threading.Thread(target=encode_and_send, args=(
      client_socket1, frame_queue1), daemon=True)
  encode_thread2 = threading.Thread(target=encode_and_send, args=(
      client_socket2, frame_queue2), daemon=True)

  encode_thread1.start()
  encode_thread2.start()

  # カメラ処理を別スレッドで実行
  thread1 = threading.Thread(target=capture_camera, args=(0, frame_queue1))
  thread2 = threading.Thread(target=capture_camera, args=(2, frame_queue2))

  thread1.start()
  thread2.start()

  cnc = conection()
  cnc.ser.flash
  cnc.sv.bind((cnc.socketsetting[ip], cnc.socketsetting[sendport]))
  cnc.sv.listen()
  z = 0
  while True:
    client, addr = cnc.sv.accept()
    try:
      # 別スレッドでクライアントに返答
      with ThreadPoolExecutor(max_workers=4) as executor:
        cnc.data_get[z] = executor.submit(
            cnc.responseToCommand, client, addr)
        cnc.data_return.append(data_get[z].result())
        cnc.contime.append(cnc.data_return[-1].pop(-1))
  #       try:
        print(data_return)
        cnc.serialtusin()

        if (not cnc.data_return[-1][:1] == "0" and not cnc.data_return[-1][:1] == "1"):
          cnc.data_return.pop(-1)
        elif (len(data_return) > 10):
          cnc.data_return.pop(0)
  #       except:
  #            print("error")

      if z > 3:
        z = 0
      else:
        z += 1
    except TimeoutError:
      print("なんかエラー出てる")

      cnc.backlog()
      continue


if __name__ == '__main__':
  main()
