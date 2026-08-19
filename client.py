import os
import socket
import threading

HOST = "127.0.0.1"   
PORT = 50000        

def thread2_receber(sock):
    buffer = ""
    try:
        while True:
            dados = sock.recv(1024)
            if not dados:                       
                print("\n[cliente] conexao encerrada pelo servidor.")
                break
            buffer += dados.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                print(linha)
    except OSError:
        pass
    finally:
        os._exit(0)

def thread1_enviar(sock):
    try:
        while True:
            texto = input()
            if texto == "":
                continue
            sock.sendall((texto + "\n").encode("utf-8"))
            if texto.strip().lower() == ":quit":
                break
    except (EOFError, OSError):
        pass
    finally:
        try:
            sock.close()
        except OSError:
            pass


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    threading.Thread(target=thread2_receber, args=(sock,), daemon=True).start()

    t1 = threading.Thread(target=thread1_enviar, args=(sock,))
    t1.start()
    t1.join()


if __name__ == "__main__":
    main()