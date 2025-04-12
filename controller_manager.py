import socket
import serial
import time
from concurrent.futures import ThreadPoolExecutor

socket.setdefaulttimeout(2.0)
# from onsei_ras import audioin

# def audio_send(ip):
#   rec = audioin()
#   rec.record()
#   rec.rec_send(ip)

class conection:
  def __init__(self):
    self.data_get = [0] * 4
    self.data_return = []
    self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    self.sv = socket.socket(socket.AF_INET)
    self.port = 36133
    self.back_port = 36132
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
    def datacheck(datacount): return datacount > 0
    if (datacheck(len(self.data_return))):
        with ThreadPoolExecutor(max_workers=4) as executor:
          setuzoku = executor.submit(self.tunagu)
          while (True):
              if (datacheck(len(self.data_return))):
                self.serialtusin()
                self.data_return.pop(-1)
                time.sleep(self.contime[-1])
                self.contime.pop(-1)
                try:
                  client = setuzoku.result(timeout=1)
                  client.close()
                except TimeoutError:
                  continue
                except:
                  print("接続エラー")
                else:
                    break
              else:
                break

  def responseToCommand(self, client, addr):
    start = time.time()
    # クライアントからのデータを受信
    data = client.recv(1024)
    comand = data.decode("utf-8")
    # サーバーからの応答を送信
    res = socket.socket(socket.AF_INET)
    res.connect((addr[0], self.back_port))
    res.send("Thank you!".encode("utf-8"))
    client.close()
    res.close()
    print(comand)
    end = time.time()
    return [comand, end - start]


def conconection():
  cnc = conection()
  cnc.ser.flush()
  cnc.sv.bind(("10.133.7.48", cnc.port))
  cnc.sv.listen()
  z = 0
  while True:
    try:
        client, addr = cnc.sv.accept()
      # クライアントからのコマンドを処理
        with ThreadPoolExecutor(max_workers=4) as executor:
          cnc.data_get[z] = executor.submit(
            cnc.responseToCommand, client, addr)
          cnc.data_return.append(cnc.data_get[z].result())
          cnc.contime.append(cnc.data_return[-1].pop(-1))
          cnc.data_return[-1] = cnc.data_return[-1][0]
          print(cnc.data_return)
          cnc.serialtusin()

          if (not cnc.data_return[-1][:1] == "0" and not cnc.data_return[-1][:1] == "1"):
              cnc.data_return.pop(-1)
          elif (len(cnc.data_return) > 10):
              cnc.data_return.pop(0)
  #       except:
  #            print("error")

          if z > 2:
                z = 0
          else:
                z += 1
    except TimeoutError:
      print("接続エラー: タイムアウト")

      cnc.backlog()
#      continue
