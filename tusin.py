# メイン
import copy
import socket
import socketmanager
import controller_get as con
import time
import pygame
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

def main():
  hat_data = [0] * 2
  botan_data = [0] * 10
  Lstick_data = [0] * 2
  Rstick_data = [0] * 2
  hat_data_old = [0] * 2
  botan_data_old = [0] * 10
  Lstick_data_old = [0] * 2
  Rstick_data_old = [0] * 2
  pygame.init()
  j = pygame.joystick.Joystick(0)
  j.init()
  # 戻り値待ち受け用のサーバ
  port = portcheck("port番号を打ち込んでください")
  back_port = portcheck("返信用のport番号を打ち込んでください")
  sv = socket.socket(socket.AF_INET)
  sv.bind((socket.gethostbyname(socket.gethostname()), back_port))
  sv.listen()

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
if __name__ == "__main__":
  main()
