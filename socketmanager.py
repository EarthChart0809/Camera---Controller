# socketmanager.py
import threading
import socket

# サーバーからの戻り値を待ち受けるスレッドメソッド
#  sv      : listen済のサーバーソケットオブジェクト(socket)
#  callback: サーバーからの戻り値文字列を処理するコールバック関数
def receiveReturn(sv, callback):
  sv.settimeout(1)  # タイムアウトを5秒に設定（調整可能）
  
  try:
        res, addr = sv.accept()   # 受信待ち
        print(f"接続受理: {addr}")

        # 返答をコールバックに返す
        data = res.recv(1024)
        str = data.decode("utf-8")
        callback(str)

  except socket.timeout:
        print("Warning: sv.accept() timed out. Retrying...")
        return  # タイムアウトしたらそのまま戻る
  except Exception as e:
        print(f"Error in receiveReturn: {e}")


# コマンドを送信して返答をコールバックする
#  client  : connect済みの送信用socketオブジェクト
#  sv      : listen済のサーバーソケットオブジェクト(socket)
#  command : 送信コマンド文字列
#  callback: サーバーからの返答文字列を受けるコールバック関数

def sendCommand(client, sv, command, callback):
  try:
        msg = command.encode("utf-8")
        client.sendall(msg)  # send() より sendall() のほうが確実
  except Exception as e:
        print(f"Error sending command: {e}")
  finally:
        client.close()  # 送信後に適切に閉じる
  # 返答をスレッドで受ける
  thre = threading.Thread(target=receiveReturn,args=(sv, callback), daemon=True)
  thre.start()
  # thre.join()
