import socket
import sys
import time
import os

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, '/app')

from app.common.config import HTTP_PORT, WEB_DOMAIN
from app.dns.client_dns import resolver_nome
from app.http.metrics import salvar_log_http

BUFFER_SIZE = 4096

def salvar_arquivo_saida(nome_recurso, dados):
    os.makedirs('/app/data/output', exist_ok=True)
    caminho = f'/app/data/output/http_{nome_recurso.replace("/","_")}'
    with open(caminho, 'wb') as f:
        f.write(dados)
    return caminho

def start_client(cenario='A', recurso='/'):
    dominio = WEB_DOMAIN
    ip_servidor, tempo_dns, status_dns = resolver_nome(dominio)

    print(f'DNS status: {status_dns}')
    print(f'DNS dominio: {dominio}')
    print(f'DNS IP: {ip_servidor if ip_servidor else "-"}')
    print(f'DNS tempo: {tempo_dns:.4f}s')

    if status_dns != 'OK':
        print('Falha na resolucao DNS')
        return

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip_servidor, HTTP_PORT))

    path = recurso if recurso.startswith('/') else f'/{recurso}'

    request = f'GET {path} HTTP/1.1\r\nHost: {dominio}\r\n\r\n'
    inicio = time.time()
    client.sendall(request.encode())

    # ler cabecalhos
    data = b''
    while b'\r\n\r\n' not in data:
        chunk = client.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk

    if not data:
        print('Sem resposta')
        client.close()
        return

    header_bytes, corpo = data.split(b'\r\n\r\n', 1)
    headers = header_bytes.decode(errors='replace').split('\r\n')
    status_line = headers[0]
    partes = status_line.split()
    status = ' '.join(partes[1:]) if len(partes) > 1 else ''

    content_length = None
    for h in headers[1:]:
        if ':' in h:
            k, v = h.split(':', 1)
            if k.strip().lower() == 'content-length':
                try:
                    content_length = int(v.strip())
                except:
                    content_length = None

    body = corpo
    # receber restante
    if content_length is not None:
        while len(body) < content_length:
            chunk = client.recv(BUFFER_SIZE)
            if not chunk:
                break
            body += chunk

    fim = time.time()
    tempo_http = fim - inicio
    tempo_total = tempo_http + tempo_dns

    caminho = salvar_arquivo_saida(recurso.strip('/'), body)
    arquivo_log = salvar_log_http('tcp', cenario, recurso, tempo_dns, tempo_total, len(body), status)

    print(f'Status HTTP: {status}')
    print(f'Tempo HTTP: {tempo_http:.4f}s')
    print(f'Tempo total (incluindo DNS): {tempo_total:.4f}s')
    print(f'Arquivo salvo em: {caminho}')
    print(f'Log salvo em: {arquivo_log}')

    client.close()

if __name__ == '__main__':
    cenario = sys.argv[1] if len(sys.argv) > 1 else 'A'
    recurso = sys.argv[2] if len(sys.argv) > 2 else '/'
    start_client(cenario, recurso)
