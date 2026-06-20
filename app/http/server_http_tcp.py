import socket
import sys
import os
import time

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, '/app')

from app.common.config import HTTP_PORT, MATRICULA, NOME
from app.common.utils import gerar_auth

HOST = '0.0.0.0'
BUFFER_SIZE = 4096
WWW_DIR = '/app/data/www'

def detectar_content_type(path):
    if path.endswith('.html'):
        return 'text/html'
    if path.endswith('.txt'):
        return 'text/plain'
    if path.endswith('.jpg') or path.endswith('.jpeg'):
        return 'image/jpeg'
    if path.endswith('.png'):
        return 'image/png'
    return 'application/octet-stream'

def montar_resposta(status_code, content=b'', content_type='application/octet-stream'):
    status_line = f'HTTP/1.1 {status_code}\r\n'
    headers = [
        f'Content-Type: {content_type}',
        f'Content-Length: {len(content)}',
        f'X-Custom-Auth: {gerar_auth(MATRICULA, NOME)}',
        '\r\n'
    ]

    return (status_line + '\r\n'.join(headers)).encode() + content

def handle_conn(conn, addr):
    try:
        data = b''
        # ler ate cabecalhos completos
        while b'\r\n\r\n' not in data:
            chunk = conn.recv(BUFFER_SIZE)
            if not chunk:
                return
            data += chunk

        request_text = data.decode(errors='replace')
        lines = request_text.split('\r\n')
        request_line = lines[0]
        parts = request_line.split()
        if len(parts) < 2:
            conn.sendall(montar_resposta('400 Bad Request', b'Bad Request', 'text/plain'))
            return

        method, path = parts[0], parts[1]

        if path.startswith('/'):
            path = path[1:]
        if path == '':
            path = 'index.html'

        file_path = os.path.join(WWW_DIR, path)

        if method != 'GET':
            conn.sendall(montar_resposta('405 Method Not Allowed', b'Method Not Allowed', 'text/plain'))
            return

        if not os.path.isfile(file_path):
            body = b'<h1>404 Not Found</h1>'
            conn.sendall(montar_resposta('404 Not Found', body, 'text/html'))
            return

        with open(file_path, 'rb') as f:
            content = f.read()

        content_type = detectar_content_type(file_path)
        conn.sendall(montar_resposta('200 OK', content, content_type))

    except Exception as e:
        print('Erro handler HTTP:', e)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, HTTP_PORT))
    server.listen(5)

    print(f'[HTTP] Servidor TCP escutando em {HOST}:{HTTP_PORT}')

    while True:
        conn, addr = server.accept()
        print(f'[HTTP] Conexao de {addr}')
        handle_conn(conn, addr)
        conn.close()

if __name__ == '__main__':
    start_server()
