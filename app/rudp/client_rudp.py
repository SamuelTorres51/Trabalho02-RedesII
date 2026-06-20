import socket
import time
import csv
import os
import sys

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, '/app')

from app.rudp.rudp import criar_pacote
from app.common.config import MATRICULA, NOME, WEB_DOMAIN
from app.common.utils import gerar_auth
from app.dns.client_dns import resolver_nome

def salvar_log(tempo, total_bytes, cenario):

    throughput = total_bytes / tempo if tempo > 0 else 0

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    arquivo_existe = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as f:

        writer = csv.writer(f)

        if not arquivo_existe:
            writer.writerow([
                "tempo",
                "bytes",
                "throughput",
                "cenario"
            ])

        writer.writerow([
            round(tempo, 2),
            total_bytes,
            round(throughput, 2),
            cenario
        ])

SERVER_HOST = ""
SERVER_PORT = 6000

BUFFER_SIZE = 1024
TIMEOUT = 0.3
MAX_TENTATIVAS = 5

CENARIO = sys.argv[1]

INPUT_FILE = "/app/data/input/arquivo_envio.bin"
LOG_FILE = f"/app/data/logs/rudp_cenario_{CENARIO}.csv" 

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client.settimeout(TIMEOUT)

ip_servidor, tempo_dns, status_dns = resolver_nome(WEB_DOMAIN)

print(f"DNS status: {status_dns}")
print(f"DNS dominio: {WEB_DOMAIN}")
print(f"DNS IP: {ip_servidor if ip_servidor else '-'}")
print(f"DNS tempo: {tempo_dns:.4f}s")

if status_dns != "OK":
    print("[CLIENTE] Falha na resolucao DNS")
    client.close()
    exit(1)

SERVER_HOST = ip_servidor

seq_num = 1

total_bytes = 0
inicio = time.time()

# Gera X-Custom-Auth com SHA-256 da matrícula + nome
AUTH_HASH = gerar_auth(MATRICULA, NOME)
AUTH_TOKEN = f"X-Custom-Auth:{AUTH_HASH}"

print("[CLIENTE] Enviando AUTH")

auth_packet = criar_pacote(
    seq_num=0,
    dados=b"AUTH",
    auth_hash=AUTH_TOKEN
)

client.sendto(auth_packet, (SERVER_HOST, SERVER_PORT))

auth_response, _ = client.recvfrom(1024)

print(f"[CLIENTE] Resposta AUTH: {auth_response.decode()}")

if auth_response.decode() != "AUTH-OK":

    print("[CLIENTE] Falha na autenticação")

    client.close()

    exit()

with open(INPUT_FILE, "rb") as f:

    while True:

        chunk = f.read(BUFFER_SIZE)

        if not chunk:
            break

        packet = criar_pacote(
            seq_num=seq_num,
            dados=chunk,
            auth_hash=AUTH_TOKEN
        )

        tentativas = 0
        ack_recebido = False

        while tentativas < MAX_TENTATIVAS and not ack_recebido:

            try:

                print(f"[CLIENTE] Enviando seq={seq_num}")

                client.sendto(packet, (SERVER_HOST, SERVER_PORT))

                ack, _ = client.recvfrom(1024)

                ack_msg = ack.decode()

                print(f"[CLIENTE] ACK recebido: {ack_msg}")

                if ack_msg == f"ACK:{seq_num}":
                    ack_recebido = True
                    total_bytes += len(chunk)

            except socket.timeout:

                tentativas += 1

                print(f"[CLIENTE] Timeout seq={seq_num}")

        if not ack_recebido:

            print("[CLIENTE] Falha na transmissão")

            break

        seq_num += 1


fin_packet = criar_pacote(
    seq_num=seq_num,
    dados=b"FIN",
    auth_hash=AUTH_TOKEN
)

tentativas = 0
fin_ack = False

while tentativas < MAX_TENTATIVAS and not fin_ack:

    try:

        client.sendto(fin_packet, (SERVER_HOST, SERVER_PORT))

        ack, _ = client.recvfrom(1024)

        ack_msg = ack.decode()

        print(f"[CLIENTE] Resposta FIN: {ack_msg}")

        if ack_msg == "FIN-ACK":
            fin_ack = True

    except socket.timeout:

        tentativas += 1

        print("[CLIENTE] Timeout FIN. Retransmitindo...")

if fin_ack:
    print("[CLIENTE] Conexão encerrada corretamente")

else:
    print("[CLIENTE] Falha ao finalizar conexão")

fim = time.time()

tempo_total = fim - inicio

throughput = total_bytes / tempo_total

print("\n===== RESULTADO =====")
print(f"Tempo total: {tempo_total:.2f}s")
print(f"Bytes enviados: {total_bytes}")
print(f"Throughput: {throughput:.2f} B/s")

salvar_log(
    tempo_total,
    total_bytes,
    CENARIO
)

client.close()