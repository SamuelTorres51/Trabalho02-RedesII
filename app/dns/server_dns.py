import socket
import sys

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, "/app")

from app.common.config import DNS_PORT
from app.dns.protocol import ler_mensagem_dns, montar_mensagem_dns


HOST = "0.0.0.0"
ZONE_FILE = "/app/data/dns/hosts.txt"
BUFFER_SIZE = 1024


def carregar_zona(caminho):
    tabela = {}

    with open(caminho, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue

            partes = linha.split()
            if len(partes) < 2:
                continue

            dominio = partes[0].lower()
            ip = partes[1]
            tabela[dominio] = ip

    return tabela


def iniciar_servidor_dns():
    tabela_zona = carregar_zona(ZONE_FILE)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind((HOST, DNS_PORT))

    print(f"[DNS] Servidor escutando em {HOST}:{DNS_PORT}")
    print(f"[DNS] Entradas carregadas: {len(tabela_zona)}")

    while True:
        dados, addr = servidor.recvfrom(BUFFER_SIZE)
        query_id, nome, _ = ler_mensagem_dns(dados)

        nome = nome.lower()
        ip = tabela_zona.get(nome, "")

        resposta = montar_mensagem_dns(query_id, nome, ip)
        servidor.sendto(resposta, addr)

        if ip:
            print(f"[DNS] {addr} -> {nome} = {ip}")
        else:
            print(f"[DNS] {addr} -> {nome} nao encontrado")


if __name__ == "__main__":
    iniciar_servidor_dns()