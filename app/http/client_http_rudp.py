import socket
import struct
import sys
import time
import os

sys.path.insert(0, '/app')

from app.common.config import WEB_DOMAIN_RUDP
from app.dns.client_dns import resolver_nome
from app.common.utils import gerar_auth
from app.rudp.rudp import criar_pacote, ler_pacote, calcular_checksum
from app.http.metrics import salvar_log_http

BUFFER_SIZE = 2048
TIMEOUT = 0.3
MAX_TENTATIVAS = 10

def ler_pacote_seguro(packet):
    try:
        return ler_pacote(packet)
    except (struct.error, IndexError, UnicodeDecodeError):
        return None


def mensagem_ack_valida(data, seq_esperado):
    try:
        return data.decode('ascii') == f'ACK:{seq_esperado}'
    except (UnicodeDecodeError, ValueError):
        return False


def salvar_arquivo_saida(nome_recurso, dados):
    os.makedirs('/app/data/output', exist_ok=True)
    caminho = f'/app/data/output/http_rudp_{nome_recurso.replace("/","_")}'
    with open(caminho, 'wb') as f:
        f.write(dados)
    return caminho

def start_client(cenario='A', recurso='/'):
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

    auth_recebido = False
    tentativas = 0


    while tentativas < MAX_TENTATIVAS and not auth_recebido:

        try:

            client.sendto(auth_packet, (ip_servidor, 6000))

            auth_response, _ = client.recvfrom(1024)

            try:
                resposta_auth = auth_response.decode('ascii')
            except (UnicodeDecodeError, ValueError):
                tentativas += 1
                print('[CLIENTE] Resposta AUTH invalida, reenviando')
                continue

            print('[CLIENTE] Resposta AUTH:', resposta_auth)

            if resposta_auth == 'AUTH-OK':
                auth_recebido = True

        except socket.timeout:

            tentativas += 1

            print(f'[CLIENTE] Timeout AUTH ({tentativas}/{MAX_TENTATIVAS})')
        
    if not auth_recebido:
        print('[CLIENTE] Falha na autenticacao')
        client.close()
        return

    inicio = time.time()

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
            if mensagem_ack_valida(ack, 1):
                print('[CLIENTE] ACK recebido: ACK:1')
                ack_recebido = True
            else:
                tentativas += 1
                print('[CLIENTE] Ignorando mensagem inesperada no request')
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


    timeouts_consecutivos = 0
    MAX_TIMEOUTS_RESPOSTA = 15
    while True:
        try:
            packet, _ = client.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            timeouts_consecutivos += 1
            print(
                f'[CLIENTE] Timeout recebendo resposta '
                f'({timeouts_consecutivos}/{MAX_TIMEOUTS_RESPOSTA})'
            )
            if timeouts_consecutivos >= MAX_TIMEOUTS_RESPOSTA:
                print('[CLIENTE] Encerrando por excesso de timeouts')
                break
            if expected_seq > 1:
                ultimo_ack = f'ACK:{expected_seq - 1}'
                client.sendto(ultimo_ack.encode(), (ip_servidor, 6000))
            continue

        parsed = ler_pacote_seguro(packet)
        if parsed is None:
            continue

        seq_num, tamanho, checksum, auth_hash, dados = parsed

        if auth_hash != AUTH_TOKEN:
            print('[CLIENTE] AUTH invalido no pacote recebido')
            continue

        if dados == b'FIN':
            client.sendto(b'FIN-ACK', (ip_servidor, 6000))
            print('[CLIENTE] FIN recebido, encerrando')
            break

        checksum_calc = calcular_checksum(dados)
        if checksum != checksum_calc:
            print('[CLIENTE] Checksum invalido seq=', seq_num)
            continue

        if seq_num == expected_seq:
            timeouts_consecutivos = 0
            corpo += dados
            ack = f'ACK:{seq_num}'
            client.sendto(ack.encode(), (ip_servidor, 6000))
            expected_seq += 1
        elif seq_num < expected_seq:
            ack = f'ACK:{seq_num}'
            client.sendto(ack.encode(), (ip_servidor, 6000))

    fim = time.time()
    tempo_http = fim - inicio
    tempo_total = tempo_dns + tempo_http

    caminho = salvar_arquivo_saida(recurso.strip('/'), corpo)
    arquivo_log = salvar_log_http('rudp', cenario, recurso, tempo_dns, tempo_total, len(corpo), '200 OK')
    print(f'Arquivo salvo em: {caminho}')
    print(f'Tempo HTTP: {tempo_http:.4f}s')
    print(f'Tempo total (incluindo DNS): {tempo_total:.4f}s')
    print(f'Log salvo em: {arquivo_log}')

    client.close()

if __name__ == '__main__':
    cenario = sys.argv[1] if len(sys.argv) > 1 else 'A'
    recurso = sys.argv[2] if len(sys.argv) > 2 else '/'
    start_client(cenario, recurso)
