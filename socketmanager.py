# socketmanager.py
import threading

# サーバーからの戻り値を待ち受けるスレッドメソッド
#  sv      : listen済のサーバーソケットオブジェクト(socket)
#  callback: サーバーからの戻り値文字列を処理するコールバック関数
def receiveReturn(sv, callback):
  res, addr = sv.accept()   # 受信待ち

  # 返答をコールバックに返す
  data = res.recv(1024)
  str = data.decode("utf-8")
  callback(str)


# コマンドを送信して返答をコールバックする
#  client  : connect済みの送信用socketオブジェクト
#  sv      : listen済のサーバーソケットオブジェクト(socket)
#  command : 送信コマンド文字列
#  callback: サーバーからの返答文字列を受けるコールバック関数

def sendCommand(client, sv, command, callback):
  msg = command.encode("utf-8")
  val = client.send(msg)
  client.close()

  # 返答をスレッドで受ける
  thre = threading.Thread(target=receiveReturn, args=(sv, callback))
  thre.start()
  thre.join()
