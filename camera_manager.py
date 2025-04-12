import tkinter
from tkinter import Button
import numpy as np
import PIL.Image
import PIL.ImageTk
import cv2
import threading
import struct
from pyzbar.pyzbar import decode, ZBarSymbol
import time

class CameraManager:
  def __init__(self, server_ip, server_port, canvas,window):
        self.server_ip = server_ip
        self.server_port = server_port
        self.canvas = canvas
        self.window = window  # **ここで Tkinter のウィンドウを管理**
        self.photo_var = [None]
        self.zoom_factor = [1]  # ズーム倍率をリストで管理
        self.zoom_lock = threading.Lock()
        self.client = None
        self.last_qr_time = 0 # QRコード取得のためのタイムスタンプ
        self.last_draw_time = 0  # 描画のためのタイムスタンプ

  # デジタルズーム関数
  def digital_zoom(self,frame, zoom_factor):
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
  def get_qr_text(self,frame: np.ndarray):
    now = time.time()
    if now - self.last_qr_time < 5:  # 5秒間隔
        return ""
    self.last_qr_time = now
    value = decode(frame, symbols=[ZBarSymbol.QRCODE])
    return '\n'.join(list(map(lambda code: code.data.decode('utf-8'), value)))

  # 各カメラのフレームを表示する関数
  def update_image(self,data, canvas, photo_var, zoom_factor, zoom_lock):
    now = time.time()
    if now - self.last_draw_time < 0.033:  # 約30fps
        return
    self.last_draw_time = now
    
    if not canvas.winfo_ismapped():  # キャンバスが表示されていない場合は処理しない
        return
    
    img = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(img, 1)
    if img is None:
        print("Failed to decode image data.")
        return
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # ズーム倍率をロックして取得
    with zoom_lock:
        zoomed_img = self.digital_zoom(img, zoom_factor[0])

    qr_text = self.get_qr_text(zoomed_img)
    if qr_text:
        print(f"QRコードが検出されました: {qr_text}")

    photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(zoomed_img))

    def update_canvas():
        canvas.create_image(0, 0, image=photo, anchor=tkinter.NW)
        photo_var[0] = photo  # メモリ上で画像を保持するために参照を保存

    self.window.after(0, update_canvas)  # **`window` ではなく `canvas` に `after` を適用**

  # 各カメラの更新ループを実行する関数
  def update_loop(self,client, canvas, photo_var, zoom_factor, zoom_lock):
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

            # print(f"受信データサイズ: {data_size} バイト")

            while len(data) < data_size:
                packet = client.recv(4096)
                if not packet:
                    return
                data += packet

            img_data = data[:data_size]
            data = data[data_size:]
        
            # **メインスレッドで画像を更新**
            self.window.after(0, self.update_image, img_data, self.canvas,
                              self.photo_var, self.zoom_factor, self.zoom_lock)

        except Exception as e:
            print(f"Error in update_loop: {e}")
            break


  