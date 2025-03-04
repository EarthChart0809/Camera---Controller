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
BUFSIZE = 4096
data_get: list[Future] = []   # 型をFutureに変更
data_return = []
port = int(input("port番号を打ち込んでください: "))
back_port = int(input("バックポート番号を打ち込んでください: "))

# シリアルポートの初期化
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
ser.flush()

# ソケットの設定
sv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sv.bind(("10.133.7.48", port))
sv.listen()

z = 0

def serialtusin(message, ser):
    msg = str(message) + "\n"
    ser.write(msg.encode('utf-8'))
    time.sleep(0.01)  # 小休止
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        print(line)

# クライアントからのコマンドを処理する関数
def responseToCommand(client, addr, back_port):
    try:
        data = client.recv(1024)
        command = data.decode("utf-8")

        # クライアントに返答
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as res:
            res.connect((addr[0], back_port))
            res.sendall("Thank you!".encode("utf-8"))

        print(command)
        return command
    except Exception as e:
        print(f"Error handling command: {e}")
        return "ERROR"
    finally:
        client.close()

# カメラ処理
def capture_camera(camera_index, client_socket):
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 手動露出
    cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # 露出調整
    cap.set(cv2.CAP_PROP_FPS, 15)  # フレームレート設定

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

                _, img_encoded = cv2.imencode('.jpg', frame)
                data = img_encoded.tobytes()

                # フレームサイズを送信
                data_size = struct.pack(">L", len(data))
                try:
                    client_socket.sendall(data_size)
                    client_socket.sendall(data)
                except Exception as e:
                    print(f"Error sending frame: {e}")
                    break  # 接続エラー時はループを抜ける

                # フレームレートの維持
                time.sleep(0.05)

    except Exception as e:
        print(f"Error in camera {camera_index}: {e}")
    finally:
        cap.release()

def command_listener():
  global z
  global data_get

  with ThreadPoolExecutor(max_workers=4) as executor:  # ループ外でExecutorを作成
      while True:
          try:
                client, addr = sv.accept()
                print(f"Accepted connection from {addr}")

                # 別スレッドでクライアントに返答
                future = executor.submit(
                    responseToCommand, client, addr, back_port)
                data_get.append(future)  # 配列の使い方を統一
                data_return.append(future.result())

                print("Received:", data_return)

                serialtusin(data_return[-1], ser)

                if not data_return[-1][:1] in ["0", "1"]:
                    data_return.pop(-1)
                elif len(data_return) > 10:
                    data_return.pop(0)

                z += 1
                if z > 3:
                    z = 0

          except Exception as e:
                print(f"Error in command_listener: {e}")
def main():

  # メイン処理
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((SERVER_IP, SERVER_PORT))
  server.listen(2)  # 2つのクライアントを待機

  print("Waiting for connection...")

  try:
    client_socket0, client_address1 = server.accept()
    print(f"Connection from: {client_address1} for Camera 0")

    client_socket1, client_address2 = server.accept()
    print(f"Connection from: {client_address2} for Camera 1")

    back_client, back_address = server.accept()
    print(f"Connection from: {back_address} for Controller")

    # カメラ処理を別スレッドで実行
    thread0 = threading.Thread(target=capture_camera, args=(0, client_socket0))
    thread1 = threading.Thread(target=capture_camera, args=(2, client_socket1))

    #コントローラー処理を別スレッドで実行
    thread2 = threading.Thread(target=command_listener)

    thread0.start()
    thread1.start()
    thread2.start()

    thread0.join()
    thread1.join()
    thread2.join()

  except KeyboardInterrupt:
    print("Shutting down server.")
  finally:
    client_socket0.close()
    client_socket1.close()
    back_client.close()
    server.close()

if __name__ =='__main__':
  main()
