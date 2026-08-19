# Multiusers Chat - Redes de Computadores (PUC-Campinas)

Repositório oficial do projeto prático da disciplina de Redes de Computadores.


Grupo:

-Beatriz Bistaffa Vitor RA:24003635

-Cauan Figueiredo Braga  RA:24787038

-Pedro Henrique Galembeck RA:24005794


## Status do Projeto: FASE 1 (Concluída)

### O que foi implementado na Fase 1:
- Conexão TCP orientada a sockets entre Cliente e Servidor.
- Uso de `threading` no cliente e no servidor para comunicação assíncrona (separando o envio por teclado do recebimento de rede).
- Tratamento de buffer de pacotes para evitar fragmentação de mensagens.
- Suporte a comandos básicos (`:quit` para sair e `:nome` para alterar o apelido).
- Envio automático da mensagem de confirmação inicial (`<HORARIO>: CONECTADO!!`).

### Como Executar e Testar

1. **Rodar o Servidor:**
   Abra dois terminais e execute:
   python servidor.py
   python cliente.py
