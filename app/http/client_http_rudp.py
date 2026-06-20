import socket
import sys
import time
import os

sys.path.insert(0, '/app')

from app.common.config import WEB_DOMAIN_RUDP
from app.dns.client_dns import resolver_nome
from app.common.utils import gerar_auth
from app.rudp.rudp import criar_pacote, ler_pacote, calcular_checksum

BUFFER_SIZE = 2048
TIMEOUT = 0.3
MAX_TENTATIVAS = 5

def salvar_arquivo_saida(nome_recurso, dados):
    os.makedirs('/app/data/output', exist_ok=True)
    caminho = f'/app/data/output/http_rudp_{nome_recurso.replace("/","_")}'
    with open(caminho, 'wb') as f:
        f.write(dados)
    return caminho

def start_client(recurso='/'):
    dominio = WEB_DOMAIN_RUDP
    ip_servidor, tempo_dns, status_dns = resolver_nome(dominio)

    print(f'DNS status: {status_dns}')
    print(f'DNS dominio: {dominio}')
    print(f'DNS IP: {ip_servidor if ip_servidor else "-"}')
    print(f'DNS tempo: {tempo_dns:.4f}s')

    if status_dns != 'OK':
        print('[CLIENTE] Falha na resolucao DNS')
        return

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(TIMEOUT)

    AUTH_HASH = gerar_auth('20249014475','SAMUEL')
    AUTH_TOKEN = f'X-Custom-Auth:{AUTH_HASH}'

    # handshake AUTH
    auth_packet = criar_pacote(seq_num=0, dados=b'AUTH', auth_hash=AUTH_TOKEN)
    client.sendto(auth_packet, (ip_servidor, 6000))

    try:
        auth_response, _ = client.recvfrom(1024)
        print('[CLIENTE] Resposta AUTH:', auth_response.decode())
    except socket.timeout:
        print('[CLIENTE] Timeout AUTH')
        client.close()
        return

    if auth_response.decode() != 'AUTH-OK':
        print('[CLIENTE] Falha na autenticacao')
        client.close()
        return

    # enviar request
    path = recurso if recurso.startswith('/') else f'/{recurso}'
    request = f'GET {path} HTTP/1.1\r\nHost: {dominio}\r\n\r\n'.encode()

    packet = criar_pacote(seq_num=1, dados=request, auth_hash=AUTH_TOKEN)

    tentativas = 0
    ack_recebido = False

    while tentativas < MAX_TENTATIVAS and not ack_recebido:
        try:
            print('[CLIENTE] Enviando request')
            client.sendto(packet, (ip_servidor, 6000))
            ack, _ = client.recvfrom(1024)
            ack_msg = ack.decode()
            print('[CLIENTE] ACK recebido:', ack_msg)
            if ack_msg == 'ACK:1':
                ack_recebido = True
        except socket.timeout:
            tentativas += 1
            print('[CLIENTE] Timeout request')

    if not ack_recebido:
        print('[CLIENTE] Falha no envio do request')
        client.close()
        return

    # receber resposta
    expected_seq = 1
    corpo = b''

    while True:
        try:
            packet, _ = client.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            print('[CLIENTE] Timeout recebendo resposta')
            break

        seq_num, tamanho, checksum, auth_hash, dados = ler_pacote(packet)

        if auth_hash != AUTH_TOKEN:
            print('[CLIENTE] AUTH invalido no pacote recebido')
            continue

        if dados == b'FIN':
            # envia FIN-ACK
            client.sendto(b'FIN-ACK', (ip_servidor, 6000))
            print('[CLIENTE] FIN recebido, encerrando')
            break

        checksum_calc = calcular_checksum(dados)
        if checksum != checksum_calc:
            print('[CLIENTE] Checksum invalido seq=', seq_num)
            continue

        if seq_num == expected_seq:
            corpo += dados
            ack = f'ACK:{seq_num}'
            client.sendto(ack.encode(), (ip_servidor, 6000))
            expected_seq += 1
        else:
            # pacote duplicado ou fora de ordem, reenviar ack do ultimo recebido
            ack = f'ACK:{seq_num}'
            client.sendto(ack.encode(), (ip_servidor, 6000))

    caminho = salvar_arquivo_saida(recurso.strip('/'), corpo)
    print(f'Arquivo salvo em: {caminho}')

    client.close()

if __name__ == '__main__':
    recurso = sys.argv[1] if len(sys.argv) > 1 else '/'
    start_client(recurso)
