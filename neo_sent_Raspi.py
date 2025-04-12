import queue
import socket
import cv2
import numpy as np
import serial
import struct
import time
import threading
import controller_manager

SERVER_IP = '10.133.7.48'
SERVER_PORT = 36131

BUFSIZE = 4096
socket.setdefaulttimeout(1000)

# 繧ｭ繝･繝ｼ繧剃ｽ懈・・医お繝ｳ繧ｳ繝ｼ繝牙ｾ・■縺ｮ逕ｻ蜒上ヵ繝ｬ繝ｼ繝繧呈ｼ邏搾ｼ・
frame_queue = queue.Queue(maxsize=5)  # 繧ｭ繝･繝ｼ縺ｮ繧ｵ繧､繧ｺ繧帝←蛻・↓險ｭ螳・

def encode_and_send(client_socket, frame_queue):
    "逕ｻ蜒上ｒ繧ｨ繝ｳ繧ｳ繝ｼ繝峨＠縺ｦ騾∽ｿ｡・亥挨繧ｹ繝ｬ繝・ラ縺ｧ蜃ｦ逅・ｼ・"
    while True:
        try:
            frame = frame_queue.get()  # 繧ｭ繝･繝ｼ縺九ｉ繝輔Ξ繝ｼ繝繧貞叙蠕・            
            if frame is None:
                break  # None繧貞女縺大叙縺｣縺溘ｉ繧ｹ繝ｬ繝・ラ邨ゆｺ・
            # **JPEG 縺ｫ繧ｨ繝ｳ繧ｳ繝ｼ繝会ｼ亥悸邵ｮ邇・ｒ隱ｿ謨ｴ・・*
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),50]  # 逕ｻ雉ｪ 50 縺ｫ險ｭ螳夲ｼ・0 縺九ｉ蠕ｮ隱ｿ謨ｴ・・            
            _, img_encoded = cv2.imencode('.jpg', frame, encode_param)
            data = img_encoded.tobytes()

            # **繝輔Ξ繝ｼ繝繧ｵ繧､繧ｺ繧帝∽ｿ｡**
            data_size = struct.pack(">L", len(data))
            client_socket.sendall(data_size)
            client_socket.sendall(data)

        except Exception as e:
            print(f"Error in encode_and_send: {e}")
            break

def capture_camera(camera_index,frame_queue):
    "繧ｫ繝｡繝ｩ繧ｭ繝｣繝励メ繝｣・医Γ繧､繝ｳ繧ｹ繝ｬ繝・ラ縺ｧ蜃ｦ逅・ｼ・"
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # 隗｣蜒丞ｺｦ繧剃ｸ九￡縺ｦ霆ｽ驥丞喧
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # 繝舌ャ繝輔ぃ繧貞ｰ上＆縺上＠縺ｦ驕・ｻｶ繧呈ｸ帙ｉ縺・    
    cap.set(cv2.CAP_PROP_FPS, 15)  # FPS繧剃ｸ九￡縺ｦCPU雋闕ｷ繧定ｻｽ貂・
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # # **TCP騾壻ｿ｡縺ｮ譛驕ｩ蛹・*
    # client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 蜊ｳ譎る∽ｿ｡
    # client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)  # 騾∽ｿ｡繝舌ャ繝輔ぃ繧ｵ繧､繧ｺ繧貞ｰ上＆縺・    
    # # client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)  # 蜿嶺ｿ｡繝舌ャ繝輔ぃ繧ｵ繧､繧ｺ繧貞ｰ上＆縺・    # 
    # client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # KeepAlive繧呈怏蜉ｹ蛹・
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

            # **繝輔Ξ繝ｼ繝繧偵く繝･繝ｼ縺ｫ霑ｽ蜉・医お繝ｳ繧ｳ繝ｼ繝峨せ繝ｬ繝・ラ縺悟・逅・ｼ・*
            if not frame_queue.full():  # 繧ｭ繝･繝ｼ縺梧ｺ譚ｯ縺ｪ繧峨せ繧ｭ繝・・縺励※譛譁ｰ繝輔Ξ繝ｼ繝繧貞━蜈・                
              frame_queue.put(frame)

    except Exception as e:
        print(f"Error in capture_camera {camera_index}: {e}")
    finally:
        cap.release()
        frame_queue.put(None)  # 繧ｨ繝ｳ繧ｳ繝ｼ繝峨せ繝ｬ繝・ラ繧堤ｵゆｺ・＆縺帙ｋ


def main():

  # 繝｡繧､繝ｳ蜃ｦ逅・  
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((SERVER_IP, SERVER_PORT))
  server.listen(2)  # 2縺､縺ｮ繧ｯ繝ｩ繧､繧｢繝ｳ繝医ｒ蠕・ｩ・

  print("Waiting for connection...")

  client_socket1, client_address1 = server.accept()
  print(f"Connection from: {client_address1} for Camera 1")

  client_socket2, client_address2 = server.accept()
  print(f"Connection from: {client_address2} for Camera 2")

  # **繧ｫ繝｡繝ｩ縺斐→縺ｮ繝輔Ξ繝ｼ繝繧ｭ繝･繝ｼ繧剃ｽ懈・**
  frame_queue1 = queue.Queue(maxsize=5)
  frame_queue2 = queue.Queue(maxsize=5)

  # **繧ｨ繝ｳ繧ｳ繝ｼ繝牙ｰら畑繧ｹ繝ｬ繝・ラ繧帝幕蟋・*
  encode_thread1 = threading.Thread(target=encode_and_send, args=(
      client_socket1, frame_queue1), daemon=True)
  encode_thread2 = threading.Thread(target=encode_and_send, args=(
      client_socket2, frame_queue2), daemon=True)

  encode_thread1.start()
  encode_thread2.start()

  # 繧ｫ繝｡繝ｩ蜃ｦ逅・ｒ蛻･繧ｹ繝ｬ繝・ラ縺ｧ螳溯｡・  
  thread1 = threading.Thread(target=capture_camera, args=(0, frame_queue1))
  thread2 = threading.Thread(target=capture_camera, args=(2, frame_queue2))

  thread1.start()
  thread2.start()

  controller_manager.conconection()

if __name__ == '__main__':
  main()
