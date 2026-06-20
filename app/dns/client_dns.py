import socket
import sys
import time

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, "/app")

from app.common.config import DNS_HOST, DNS_PORT
from app.dns.protocol import ler_mensagem_dns, montar_mensagem_dns


TIMEOUT = 1.0
BUFFER_SIZE = 1024


def resolver_nome(nome, timeout=TIMEOUT):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cliente.settimeout(timeout)

    query_id = str(int(time.time() * 1000))
    payload = montar_mensagem_dns(query_id, nome)

    inicio = time.time()

    try:
        cliente.sendto(payload, (DNS_HOST, DNS_PORT))
        resposta, _ = cliente.recvfrom(BUFFER_SIZE)
    except socket.timeout:
        cliente.close()
        return "", 0.0, "TIMEOUT"

    fim = time.time()
    cliente.close()

    resposta_id, resposta_nome, ip = ler_mensagem_dns(resposta)

    if resposta_id != query_id or resposta_nome.lower() != nome.lower():
        return "", fim - inicio, "RESPOSTA_INVALIDA"

    if not ip:
        return "", fim - inicio, "NAO_ENCONTRADO"

    return ip, fim - inicio, "OK"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 app/dns/client_dns.py <dominio>")
        sys.exit(1)

    dominio = sys.argv[1]
    ip, tempo_dns, status = resolver_nome(dominio)

    print(f"Status DNS: {status}")
    print(f"Dominio: {dominio}")
    print(f"IP: {ip if ip else '-'}")
    print(f"Tempo DNS: {tempo_dns:.4f}s")