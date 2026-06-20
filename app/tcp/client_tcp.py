import socket
import time
import os
import csv
import sys

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, '/app')

from app.common.config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE, MATRICULA, NOME
from app.common.utils import gerar_auth
from app.dns.client_dns import resolver_nome
from app.common.config import WEB_DOMAIN

INPUT_FILE = "/app/data/input/arquivo_envio.bin"
CENARIO = sys.argv[1]

LOG_FILE = f"/app/data/logs/tcp_cenario_{CENARIO}.csv"
AUTH_HASH = gerar_auth(MATRICULA, NOME)


def montar_mensagem(tipo, corpo=b""):
    if isinstance(corpo, str):
        corpo = corpo.encode()

    cabecalhos = [
        f"X-Custom-Auth: {AUTH_HASH}",
        f"Type: {tipo}",
        f"Content-Length: {len(corpo)}",
    ]

    return ("\n".join(cabecalhos) + "\n\n").encode() + corpo

def salvar_log(tempo, bytes_enviados, cenario):
    throughput = bytes_enviados / tempo if tempo > 0 else 0

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
            bytes_enviados,
            round(throughput, 2),
            cenario
        ])

def start_client():
    ip_servidor, tempo_dns, status_dns = resolver_nome(WEB_DOMAIN)

    print(f"DNS status: {status_dns}")
    print(f"DNS dominio: {WEB_DOMAIN}")
    print(f"DNS IP: {ip_servidor if ip_servidor else '-'}")
    print(f"DNS tempo: {tempo_dns:.4f}s")

    if status_dns != "OK":
        print("Falha na resolucao DNS")
        return

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip_servidor, SERVER_PORT))

    client.sendall(montar_mensagem("AUTH"))

    resposta_auth = client.recv(1024).decode(errors="replace")
    print("Resposta AUTH:", resposta_auth.strip())

    if resposta_auth.strip() != "AUTH-OK":
        print("Falha na autenticação")
        client.close()
        return

    inicio = time.time()
    total_bytes = 0

    with open(INPUT_FILE, "rb") as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break

            client.sendall(montar_mensagem("DATA", data))
            total_bytes += len(data)

    client.sendall(montar_mensagem("FIN"))

    resposta_fin = client.recv(1024).decode(errors="replace")
    print("Resposta FIN:", resposta_fin.strip())

    fim = time.time()
    tempo_total = fim - inicio

    print(f"Tempo: {tempo_total:.4f}s")
    print(f"Bytes: {total_bytes}")
    print(f"Throughput: {total_bytes / tempo_total:.2f} B/s")

    salvar_log(tempo_total, total_bytes, CENARIO)

    client.close()

if __name__ == "__main__":
    start_client()