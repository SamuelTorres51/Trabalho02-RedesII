import socket
import struct
import sys
import os

sys.path.insert(0, '/app')

from app.common.config import MATRICULA, NOME
from app.common.utils import gerar_auth
from app.rudp.rudp import ler_pacote, criar_pacote, calcular_checksum

HOST = '0.0.0.0'
PORT = 6000
BUFFER_SIZE = 2048
TIMEOUT = 0.3
MAX_TENTATIVAS = 10
WWW_DIR = '/app/data/www'

EXPECTED_AUTH = f"X-Custom-Auth:{gerar_auth(MATRICULA, NOME)}"


def montar_http_response_bytes(path):
    if path.startswith('/'):
        path = path[1:]
    if path == '':
        path = 'index.html'

    file_path = os.path.join(WWW_DIR, path)

    if not os.path.isfile(file_path):
        body = b'<h1>404 Not Found</h1>'
        headers = f'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: {len(body)}\r\nX-Custom-Auth: {gerar_auth(MATRICULA, NOME)}\r\n\r\n'
        return headers.encode() + body

    with open(file_path, 'rb') as f:
        content = f.read()

    content_type = 'application/octet-stream'
    if file_path.endswith('.html'):
        content_type = 'text/html'

    headers = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\nX-Custom-Auth: {gerar_auth(MATRICULA, NOME)}\r\n\r\n'
    return headers.encode() + content


def processar_mensagem_cliente(sock, data, addr, ack_esperado=None, esperar_fin_ack=False):
    """
    Interpreta ACK/FIN-ACK em texto ou pacotes R-UDP (AUTH, FIN).
    Retorna: 'ACK_OK', 'FIN_ACK_OK', 'AUTH' ou None.
    """
    try:
        msg = data.decode('ascii')
        if esperar_fin_ack and msg == 'FIN-ACK':
            return 'FIN_ACK_OK'
        if ack_esperado is not None and msg == f'ACK:{ack_esperado}':
            return 'ACK_OK'
        return None
    except (UnicodeDecodeError, ValueError):
        pass

    if len(data) < 16:
        return None

    try:
        seq_num, tamanho, checksum, auth_hash, dados = ler_pacote(data)
    except (struct.error, IndexError, UnicodeDecodeError):
        return None

    if auth_hash != EXPECTED_AUTH:
        return None

    if dados == b'AUTH':
        sock.sendto(b'AUTH-OK', addr)
        print('[R-HTTP] AUTH recebido durante transferencia, respondendo AUTH-OK')
        return 'AUTH'

    return None


def enviar_com_retransmissoes(sock, addr, auth_token, payload):
    # envia payload em pacotes sequenciais com stop-and-wait
    seq = 1
    offset = 0
    timeout_anterior = sock.gettimeout()

    while offset < len(payload):
        chunk = payload[offset:offset + 1024]
        packet = criar_pacote(seq_num=seq, dados=chunk, auth_hash=auth_token)

        tentativas = 0
        ack_recebido = False

        while tentativas < MAX_TENTATIVAS and not ack_recebido:
            try:
                sock.sendto(packet, addr)
                sock.settimeout(TIMEOUT)
                resposta, origem = sock.recvfrom(1024)
                if origem != addr:
                    continue

                resultado = processar_mensagem_cliente(
                    sock, resposta, addr, ack_esperado=seq
                )
                if resultado == 'ACK_OK':
                    ack_recebido = True
                elif resultado == 'AUTH':
                    sock.settimeout(timeout_anterior)
                    return 'AUTH'
                else:
                    tentativas += 1
            except socket.timeout:
                tentativas += 1

        if not ack_recebido:
            sock.settimeout(timeout_anterior)
            print('[R-HTTP] Falha ao enviar pacote seq=', seq)
            return False

        seq += 1
        offset += len(chunk)

    fin_packet = criar_pacote(seq_num=seq, dados=b'FIN', auth_hash=auth_token)
    tentativas = 0
    fin_ack = False

    while tentativas < MAX_TENTATIVAS and not fin_ack:
        try:
            sock.sendto(fin_packet, addr)
            sock.settimeout(TIMEOUT)
            resposta, origem = sock.recvfrom(1024)
            if origem != addr:
                continue

            resultado = processar_mensagem_cliente(
                sock, resposta, addr, esperar_fin_ack=True
            )
            if resultado == 'FIN_ACK_OK':
                fin_ack = True
            elif resultado == 'AUTH':
                sock.settimeout(timeout_anterior)
                return 'AUTH'
            else:
                tentativas += 1
        except socket.timeout:
            tentativas += 1

    sock.settimeout(timeout_anterior)
    return fin_ack


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    server.settimeout(None)

    print(f'[R-HTTP] Servidor R-UDP escutando em {HOST}:{PORT}')

    while True:
        try:
            packet, addr = server.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            continue
        seq_num, tamanho, checksum, auth_hash, dados = ler_pacote(packet)

        if auth_hash != EXPECTED_AUTH:
            print('[R-HTTP] AUTH invalido de', addr)
            continue

        # handshake AUTH
        if dados == b'AUTH':
            server.sendto(b'AUTH-OK', addr)
            print('[R-HTTP] AUTH-OK para', addr)
            continue

        # request do cliente
        try:
            request_text = dados.decode(errors='replace')
            request_line = request_text.splitlines()[0]
            parts = request_line.split()
            if len(parts) >= 2 and parts[0] == 'GET':
                path = parts[1]
            else:
                path = '/'
        except Exception:
            path = '/'

        # confirma recebimento do request
        ack = f'ACK:{seq_num}'
        server.sendto(ack.encode(), addr)

        print(f'[R-HTTP] Requisicao {path} de {addr}, preparando resposta')

        auth_token = auth_hash
        response_bytes = montar_http_response_bytes(path)

        resultado = enviar_com_retransmissoes(server, addr, auth_token, response_bytes)

        if resultado == 'AUTH':
            print('[R-HTTP] Transferencia interrompida por novo AUTH')
            continue
        if resultado:
            print('[R-HTTP] Resposta enviada para', addr)
        else:
            print('[R-HTTP] Falha ao enviar resposta para', addr)


if __name__ == '__main__':
    start_server()
