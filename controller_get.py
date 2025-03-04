import time
import pygame
import socket
import socketmanager

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
HV = 2
HW = 3
BOTAN = 4
VARTICAL = 0
WIDTH = 1
HAT_NUMBER = 0
IP = "10.133.7.48"

def contorollerdata_send(cmd, sendc, kind, sv, port):
  command = str(kind) + "," + str(sendc) + "," + str(cmd)
  client = socket.socket(socket.AF_INET)
  try:
    client.connect((IP, port))
    print("OK")
    socketmanager.sendCommand(client, sv, command, print)
  except:
    input("Failed connection. Press enter to retry.")
    
def gethat(sv, port, j):
  hat_value[VARTICAL], hat_value[WIDTH] = j.get_hat(HAT_NUMBER)
  hat_value[VARTICAL] = int(round(hat_value[VARTICAL] * STICK_VAULE))
  hat_value[WIDTH] = int(round(hat_value[WIDTH] * STICK_VAULE))
  return hat_value


def getstick(stick_width, stick_vartical, sv, port, j):
  if abs(j.get_axis(stick_vartical)) >= STICK_PLAY or abs(j.get_axis(stick_width)) >= STICK_PLAY:
    sendstick[WIDTH] = int(
        round(j.get_axis(stick_vartical) * STICK_VAULE))
    sendstick[VARTICAL] = int(
        round(j.get_axis(stick_width) * STICK_VAULE))
  else:
      sendstick[WIDTH] = 0
      sendstick[VARTICAL] = 0
  return sendstick

def getbotan(sv, port, j):  # ボタンのデータを受け取ってsendbotanに代入する関数

  try:
    for count_btn in range(NUMBEROFBOTTONS):
      botan_value[count_btn] = j.get_button(count_btn)
    return botan_value
  except TypeError:
    pass
  return botan_value

# class controller(self):
#   def __init__(self):
#     pygame.init()
#     self.j = pygame.joystick.Joystick(0)
#     self.j.init()
#     self.axis_value = [[0, 0], [0, 0]]
#     self.botan_value = [0] * 10
#     self.hat_value = [0, 0]

#   def event(self):
#     events = self.py
