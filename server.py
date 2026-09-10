from datetime import datetime
import socket
import threading
import queue
import time
import sys

HOST = '127.0.0.1'
PORT = 50000
INTERVALO_DATA = 60



# ---- MEMORIA COMPARTILHADA (valida para TODAS as threads) ----

clientes = []    # lista de todos os clientes conectados
clientes_lock = threading.Lock()  #mutex que impede que duas threads mexam na lista ao mesmo tempo 


def enviar(conexao, texto, encerrar):
    try:
        conexao.send(texto.encode('utf-8'))
    except OSError:
        encerrar.set()


def broadcast(remetente_conexao, nome, msg):  #Mensagem publica: vai para TODOS os conectados  
    hora = datetime.now().strftime('%H:%M:%S')
    linha_fmt = f"{nome} ({hora}): {msg}\n"
    with clientes_lock:
        alvos = list(clientes)     # copia rapidinho, DENTRO da trava
        # aqui a trava ja foi solta
    for ctx in alvos:
        if ctx["conexao"] is remetente_conexao:
            enviar(ctx["conexao"], f"Voce digitou: {msg}\n", ctx["encerrar"])   # eco pro remetente
        else:
            enviar(ctx["conexao"], linha_fmt, ctx["encerrar"])                  # demais recebem formatado


def thread_receptora(conexao, endereco, fila, encerrar):   #recebe e só guarda
    buffer = ""
    try:
        while not encerrar.is_set():
            dados = conexao.recv(1024)
            if not dados:
                break
            buffer += dados.decode('utf-8', errors='ignore')
            while "\n" in buffer:  #corta o \n e organiza os bytes soltos 
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if linha:
                    fila.put(linha) #só armazena o comando
                    
    except OSError:
        pass
    finally:
        encerrar.set()  #avisa a thread2 - threa_processadora() pra para tbm 


def processar(conexao, endereco, estado, linha, encerrar):
    print(f"[{estado['nome_user']}] enviou: {linha}")
    tokens = linha.split()
    if not tokens:   #linha vazia: ignora pra nao quebrar em tokens[0]
        return

    if tokens[0].lower() == ":quit":  #encerrar conexao
        print(f"[servidor] Usuário {estado['nome_user']} desconectou.")
        encerrar.set()
        try:
            conexao.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conexao.close()
        return

    if tokens[0].lower() == ":nome":   #mudança de nome 
        if len(tokens) >= 2:
            estado['nome_user'] = linha.split(" ", 1)[1].strip()
            hora = datetime.now().strftime('%H:%M:%S')
            enviar(conexao, f"<{hora}>: Nome alterado para {estado['nome_user']}\n", encerrar)
        else:
            enviar(conexao, "[servidor] Uso correto: :nome <NOVO_NOME>\n", encerrar)
        return

    if tokens[0].startswith(":"):   #tentativa de comando 
        enviar(conexao, f"[servidor] Comando desconhecido: {tokens[0]}\n", encerrar)
        return

   
    broadcast(conexao, estado['nome_user'], linha)      # mensagem publica -> vai para todos (broadcast)

def thread_processadora(conexao, endereco, fila, estado, encerrar):  #processa + relógio
    ultimo_envio = time.monotonic()
    try:
        while not encerrar.is_set():
            try:
                linha = fila.get(timeout=1.0) # tenta pegar um comando (espera ate 1s)
                processar(conexao, endereco, estado, linha, encerrar)  # se veio, processa
            except queue.Empty:
                pass

            if time.monotonic() - ultimo_envio >= INTERVALO_DATA:  # ja passaram 60s?
                ultimo_envio = time.monotonic()
                agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                enviar(conexao, f"[servidor] {agora}\n", encerrar)   # manda a data/hora
    except OSError:
        pass
    finally:
        encerrar.set()


def lidar_com_cliente(conexao, endereco, limite):  
    estado = {"nome_user": f"{endereco[0]}:{endereco[1]}"}   # privado a cada cliente
    encerrar = threading.Event()                             # Enquanto encerrar.is_set() for False, as threads rodam; quando alguém chama encerrar.set(), todas param.
    ctx = {"conexao": conexao, "endereco": endereco, "estado": estado, "encerrar": encerrar} #empacota tudo desse cliente num só objeto, pra guardar na lista compartilhada.

   
    with clientes_lock:  #checagem do limite a trava garante que um faz tudo antes do outro começar
        if len(clientes) >= limite:
            cheio = True
        else:
            clientes.append(ctx)          # ocupa uma vaga
            cheio = False
            ativos = len(clientes)

    if cheio:
        try:
            conexao.send("[servidor] Limite de clientes atingido. Tente mais tarde.\n".encode('utf-8'))
            conexao.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conexao.close()
        print(f"[servidor] Conexão de {endereco} RECUSADA (limite atingido).")
        return

    print(f"[servidor] Nova conexão aceita de {endereco}. Clientes ativos: {ativos}")

    fila = queue.Queue()                                     # memória compartilhada entre as duas threads deste cliente
    agora = datetime.now().strftime('%H:%M:%S')            
    conexao.send(f"<{agora}>: CONECTADO!!\n".encode('utf-8'))

    t1 = threading.Thread(target=thread_receptora,args=(conexao, endereco, fila, encerrar))
    t2 = threading.Thread(target=thread_processadora,args=(conexao, endereco, fila, estado, encerrar))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    with clientes_lock: #libera a vaga e desaloca este cliente
        if ctx in clientes:
            clientes.remove(ctx)
        ativos = len(clientes)
    try:
        conexao.close()
    except OSError:
        pass
    print(f"[servidor] Conexão com {endereco} encerrada. Clientes ativos: {ativos}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python servidor.py <limite_de_clientes>")
        sys.exit(1)

    limite = int(sys.argv[1])

    if limite < 1:
        print("O limite precisa ser no minimo 1.")
        sys.exit(1)
   

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))  #prende o socket ao IP e porta
    server_socket.listen() #põe o socket em modo passivo.Ele não bloqueia nada; só avisa o sistema "estou aberto pra conexões".
    print(f"[servidor] Servidor iniciado. Escutando em {HOST}:{PORT} (limite: {limite})")
    try:
        while True:
            conexao, endereco = server_socket.accept() #bloqueia — a execução nessa linha até alguém conectar. Devolve dois valores: conexao (o socket novo, exclusivo pra falar com aquele cliente) e endereco (a tupla (IP, porta) do cliente)
            threading.Thread(target=lidar_com_cliente, args=(conexao, endereco, limite)).start()    #Cria uma thread de trabalhopara cuidar desse cliente e volta para o accept
    except KeyboardInterrupt:  # Ctrl + C
        print("\n[servidor] Servidor encerrado pelo usuário.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()