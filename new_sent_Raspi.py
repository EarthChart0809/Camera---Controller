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
data_get: list[Future] = [0]*4   # 型をFutureに変更
data_return = []

# シリアルポートの初期化
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
ser.flush()

z = 0

def serialtusin(message, ser):
    print(f"Sending message to serial: {message}")
    msg = str(message) + "\n"
    ser.write(msg.encode('utf-8'))
    time.sleep(0.01)  # 小休止
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        print(line)

# クライアントからのコマンドを処理する関数
def responseToCommand(client, addr, SERVER_PORT_CONTROLLER):
    SERVER_PORT_CONTROLLER = 36132
    try:
        print("Waiting to receive data from client...")
        data = client.recv(1024)
        command = data.decode("utf-8")
        print(f"Received command: {command}")

        # クライアントに返答
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as res:
            print(f"Connecting to {addr[0]}:{SERVER_PORT_CONTROLLER} to send response...")
            res.connect((addr[0], SERVER_PORT_CONTROLLER))
            res.sendall("Thank you!".encode("utf-8"))
            print("Sent response: Thank you!")


        print(command)
        return command
    except Exception as e:
        print(f"Error handling command: {e}")
        return "ERROR"


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

def capture_camera(camera_index, client_socket):
    """カメラキャプチャ（メインスレッドで処理）"""
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # 解像度を下げて軽量化
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # バッファを小さくして遅延を減らす
    cap.set(cv2.CAP_PROP_FPS, 15)  # FPSを下げてCPU負荷を軽減

    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}.")
        return

    # **カメラごとのフレームキューを作成**
    frame_queue = queue.Queue(maxsize=5)

    # **エンコード専用スレッドを開始**
    encode_thread = threading.Thread(
        target=encode_and_send, args=(client_socket, frame_queue), daemon=True)
    encode_thread.start()

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
        encode_thread.join()   # スレッドの終了を待つ


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

  # カメラ処理を別スレッドで実行
  thread0 = threading.Thread(target=capture_camera, args=(0, client_socket1))
  thread1 = threading.Thread(target=capture_camera, args=(2, client_socket2))

  thread0.start()
  thread1.start()

  with ThreadPoolExecutor(max_workers=2) as executor:  # ループ外でExecutorを作成
      while True:
          try:
              # **タイムアウトを使い、データが来ない場合は処理をスキップ**
              try:
                    client, addr = sv.accept()
                    print(f"Accepted connection from {addr}")
              except socket.timeout:
                    continue  # **タイムアウトしたらループを継続**

              # 別スレッドでクライアントに返答
              data_get[z] = executor.submit(
                  responseToCommand, client, addr, SERVER_PORT_CONTROLLER)
              data_return.append(data_get[z].result())

#       try:
              print(data_return)
              serialtusin(data_return[-1], ser)

              if (not data_return[-1][:1] == "0" and not data_return[-1][:1] == "1"):
                data_return.pop(-1)
              elif (len(data_return) > 10):
                data_return.pop(0)
#       except:
#            print("error")

              z += 1
              if z > 3:
                z = 0
  
          except Exception as e:
              print(f"Error in command_listener: {e}")

if __name__ =='__main__':
  main()
