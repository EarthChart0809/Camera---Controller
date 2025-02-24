import socket
import cv2
import numpy as np
import struct
import time
import threading

SERVER_IP = '172.20.10.2'
SERVER_PORT = 36131
BUFSIZE = 4096

# カメラを初期化する関数
def capture_camera(camera_index, client_socket):
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # 露出とフレームレートの設定
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 手動露出に切り替え
    cap.set(cv2.CAP_PROP_EXPOSURE, -6)         # 露出の調整（適宜調整可能）
    cap.set(cv2.CAP_PROP_FPS, 15)              # フレームレートを15fpsに設定

    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"Error: Failed to capture image from camera {camera_index}.")
                time.sleep(0.05)
                continue

            # フレームをJPEG形式にエンコード
            _, img_encoded = cv2.imencode('.jpg', frame)
            data = img_encoded.tobytes()

            # フレームサイズを送信
            data_size = struct.pack(">L", len(data))
            client_socket.sendall(data_size)

            # フレームデータを送信
            client_socket.sendall(data)

            # フレームレートを制御
            time.sleep(0.05)
    except Exception as e:
        print(f"Error in camera {camera_index}: {e}")
    finally:
        cap.release()

# ソケットの作成とバインド
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((SERVER_IP, SERVER_PORT))
server.listen(2)  # クライアントを2つ待機（2台のカメラ）
print("Waiting for connection...")


# クライアントの接続を待機
client_socket1, client_address1 = server.accept()
print(f"Connection from: {client_address1} for Camera 0")

client_socket2, client_address2 = server.accept()
print(f"Connection from: {client_address2} for Camera 1")


# カメラごとに別スレッドで映像送信
thread1 = threading.Thread(target=capture_camera, args=(0, client_socket1))
thread2 = threading.Thread(target=capture_camera, args=(2, client_socket2))

thread1.start()
thread2.start()

thread1.join()
thread2.join()

# 接続を閉じる
client_socket1.close()
client_socket2.close()
server.close()
