from datetime import datetime
import socket
import threading
import queue
import time

HOST = '127.0.0.1'
PORT = 50000
INTERVALO_DATA = 60


def enviar(conexao, texto, encerrar):
    try:
        conexao.send(texto.encode('utf-8'))
    except OSError:
        encerrar.set()


def thread_receptora(conexao, endereco, fila, encerrar):
    buffer = ""
    try:
        while not encerrar.is_set():
            dados = conexao.recv(1024)
            if not dados:            
                break
            buffer += dados.decode('utf-8', errors='ignore')
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if linha:
                    fila.put(linha)  
    except OSError:
        pass
    finally:
        encerrar.set()


def processar(conexao, endereco, estado, linha, encerrar):
    print(f"[{estado['nome_user']}] enviou: {linha}")
    tokens = linha.split()

    if tokens[0].lower() == ":quit":
        print(f"[servidor] Usuário {estado['nome_user']} desconectou.")
        encerrar.set()
        try:
            conexao.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conexao.close()
        return

    if tokens[0].lower() == ":nome":
        if len(tokens) >= 2:
            estado['nome_user'] = linha.split(" ", 1)[1].strip()
            hora = datetime.now().strftime('%H:%M:%S')
            enviar(conexao, f"<{hora}>: Nome alterado para {estado['nome_user']}\n", encerrar)
        else:
            enviar(conexao, "[servidor] Uso correto: :nome <NOVO_NOME>\n", encerrar)
        return

    hora = datetime.now().strftime('%H:%M:%S')
    enviar(conexao, f"{estado['nome_user']} ({hora}): {linha}\n", encerrar)

def thread_processadora(conexao, endereco, fila, estado, encerrar):

    ultimo_envio = time.monotonic()
    try:
        while not encerrar.is_set():
  
            try:
                linha = fila.get(timeout=1.0)
                processar(conexao, endereco, estado, linha, encerrar)
            except queue.Empty:
                pass

            if time.monotonic() - ultimo_envio >= INTERVALO_DATA:
                ultimo_envio = time.monotonic()
                agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                enviar(conexao, f"[servidor] {agora}\n", encerrar)
    except OSError:
        pass
    finally:
        encerrar.set()


def lidar_com_cliente(conexao, endereco):
    print(f"[servidor] Nova conexão aceita de {endereco}")

    fila = queue.Queue()                                   
    estado = {"nome_user": f"{endereco[0]}:{endereco[1]}"} 
    encerrar = threading.Event()                           

    agora = datetime.now().strftime('%H:%M:%S')
    conexao.send(f"<{agora}>: CONECTADO!!\n".encode('utf-8'))

    t1 = threading.Thread(target=thread_receptora,
                          args=(conexao, endereco, fila, encerrar))
    t2 = threading.Thread(target=thread_processadora,
                          args=(conexao, endereco, fila, estado, encerrar))
    t1.start()
    t2.start()

    t1.join()
    t2.join()

    try:
        conexao.close()
    except OSError:
        pass
    print(f"[servidor] Conexão com {endereco} encerrada.")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[servidor] Servidor iniciado. Escutando em {HOST}:{PORT}")
    try:
        while True:
            conexao, endereco = server_socket.accept()
            threading.Thread(target=lidar_com_cliente,
                             args=(conexao, endereco)).start()
    except KeyboardInterrupt:
        print("\n[servidor] Servidor encerrado pelo usuário.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()