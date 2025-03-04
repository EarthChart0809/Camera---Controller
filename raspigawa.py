import socket
import serial
import time
from concurrent.futures import ThreadPoolExecutor

def serialtusin(message, ser):
  msg = str(message) + "\n"
  ser.write(msg.encode('utf-8'))
  while ser.in_waiting > 0:
    print("A")
  line = ser.readline().decode('utf-8').rstrip()
  print(line)
  time.sleep(0.01)

# コマンドに対する処理と返答をする
def responseToCommand(client, addr, back_port):
  # 処理：コンソールにエコーする
  data = client.recv(1024)
  comand = data.decode("utf-8")
  # クライアントに返答
  res = socket.socket(socket.AF_INET)
  res.connect((addr[0], back_port))
  res.send("Thank you!".encode("utf-8"))
  client.close()
  res.close()
  print(comand)
  return comand


def main():
  data_get = []
  for n in range(4):
    data_get.append(0)
  data_return = []
  port = int(input("port番号を打ち込んでください"))
  back_port = int(input("port番号を打ち込んでください"))
  ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
  ser.flush
  sv = socket.socket(socket.AF_INET)
  sv.bind(("192.168.246.106", port))
  sv.listen()
  z = 0
  
  while True:

    client, addr = sv.accept()
    # 別スレッドでクライアントに返答
    with ThreadPoolExecutor(max_workers=4) as executor:
      data_get[z] = executor.submit(responseToCommand, client, addr, back_port)
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
    


if __name__ == "__main__":
  main()
