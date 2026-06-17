import socket
import random
import sys

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, '/app')

from app.rudp.rudp import ler_pacote, calcular_checksum
from app.common.config import MATRICULA, NOME
from app.common.utils import gerar_auth

HOST = "0.0.0.0"
PORT = 6000
BUFFER_SIZE = 2048

OUTPUT_FILE = "/app/data/output/arquivo_recebido_rudp.bin"

# Gera X-Custom-Auth esperado
EXPECTED_AUTH = f"X-Custom-Auth:{gerar_auth(MATRICULA, NOME)}"

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print(f"[SERVIDOR] Escutando em {HOST}:{PORT}")

expected_seq = 0

with open(OUTPUT_FILE, "wb") as arquivo:

    while True:

        packet, addr = server.recvfrom(BUFFER_SIZE)

        seq_num, tamanho, checksum, auth_hash, dados = ler_pacote(packet)
        
        # Valida autenticação
        if auth_hash != EXPECTED_AUTH:
            print(f"[ERRO] AUTH inválido: {auth_hash}")
            continue

        # HANDSHAKE AUTH
        if dados == b"AUTH":

          print(f"\n[SERVIDOR] AUTH recebido: {auth_hash}")

          server.sendto(b"AUTH-OK", addr)

          print("[SERVIDOR] AUTH-OK enviado")

          expected_seq = 1

          continue

        # PACOTE FIN
        if dados == b"FIN":

          print("\n[SERVIDOR] FIN recebido")

          server.sendto(b"FIN-ACK", addr)

          print("[SERVIDOR] FIN-ACK enviado")

          break

        checksum_calculado = calcular_checksum(dados)

        print(f"\n[SERVIDOR] Recebido seq={seq_num}")

        if checksum != checksum_calculado:

            print("[ERRO] Checksum inválido")

            continue

        # PACOTE ESPERADO
        if seq_num == expected_seq:

          arquivo.write(dados)

          print("[OK] Chunk salvo")

          ack = f"ACK:{seq_num}"

          # AVANÇA A SEQUÊNCIA IMEDIATAMENTE
          expected_seq += 1
  
          server.sendto(ack.encode(), addr)

          print(f"[SERVIDOR] ACK enviado: {ack}")

        # PACOTE DUPLICADO
        elif seq_num < expected_seq:

            print("[SERVIDOR] Duplicado")

            ack = f"ACK:{seq_num}"

            server.sendto(ack.encode(), addr)

        else:

            print("[SERVIDOR] Fora de ordem")

print("[SERVIDOR] Transferência finalizada")

server.close()