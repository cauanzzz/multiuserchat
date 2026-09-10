# Multiusers Chat - Redes de Computadores (PUC-Campinas)

Repositório oficial do projeto prático da disciplina de Redes de Computadores.

Grupo:

- Beatriz Bistaffa Vitor RA:24003635

- Cauan Figueiredo Braga RA:24787038

- Pedro Henrique Galembeck RA:24005794

## Status do Projeto: FASE 1 e FASE 2 (Concluídas)

### O que foi implementado na Fase 1:

- Conexão TCP orientada a sockets entre Cliente e Servidor.
- Uso de `threading` no cliente e no servidor para comunicação assíncrona (separando o envio por teclado do recebimento de rede).
- Tratamento de buffer de pacotes para evitar fragmentação de mensagens.
- Envio automático da mensagem de confirmação inicial (`<HORARIO>: CONECTADO!!`).
- Envio automático de data e horário a cada 1 minuto, independente de haver atividade no chat.
- Mensagens públicas: quem envia recebe o eco `Voce digitou: <MENSAGEM>` e os demais recebem no formato `NOME (horário): MENSAGEM`.
- Nome padrão automático (`IP:porta`) quando o usuário não define um apelido.
- Comandos básicos: `:nome <NOME>` para alterar o apelido e `:quit` para sair.

### O que foi implementado na Fase 2:

- Suporte a múltiplos clientes simultâneos, tratados de forma independente (uma working thread por cliente).
- Limite de clientes configurável por parâmetro na linha de comando ao iniciar o servidor.
- Liberação da vaga quando um cliente desconecta, permitindo que um novo cliente entre.
- Recusa de conexão quando o limite é atingido: o servidor envia um aviso e encerra a conexão, em vez de enviar o `CONECTADO!!`.
- Encerramento da conexão TCP e desalocação dos dados do cliente ao receber `:quit`.

### Comandos disponíveis

- `<MENSAGEM>` — qualquer texto que não comece com `:` é enviado como mensagem pública a todos.
- `:nome <NOME>` — altera o apelido do usuário.
- `:quit` — desconecta o cliente e encerra sua execução.

## Como Executar e Testar

O servidor recebe como argumento o **limite de clientes** simultâneos.

1. **Rodar o Servidor** (exemplo com limite de 2 clientes):

   ```
   python3 Server.py 2
   ```

2. **Rodar o Cliente** (em outro terminal; abra vários para simular múltiplos usuários):

   ```
   python3 Client.py
   ```

> Observação: no Windows, use `python` no lugar de `python3`.
