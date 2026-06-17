import socket
import time
import sys

# Adiciona /app ao path para imports funcionarem no Docker
sys.path.insert(0, '/app')

from app.common.config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE, MATRICULA, NOME
from app.common.utils import gerar_auth

OUTPUT_FILE = "/app/data/output/arquivo_recebido.bin"
EXPECTED_AUTH = gerar_auth(MATRICULA, NOME)


def ler_mensagem(conn, buffer):

    while b"\n\n" not in buffer:
        chunk = conn.recv(BUFFER_SIZE)
        if not chunk:
            return None, None, None, b""
        buffer += chunk

    cabecalho_bytes, corpo = buffer.split(b"\n\n", 1)
    cabecalhos = cabecalho_bytes.decode(errors="replace").splitlines()
    cabecalho_map = {}

    for linha in cabecalhos:
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            cabecalho_map[chave.strip().lower()] = valor.strip()

    comprimento = int(cabecalho_map.get("content-length", "0"))

    while len(corpo) < comprimento:
        chunk = conn.recv(BUFFER_SIZE)
        if not chunk:
            break
        corpo += chunk

    restante = corpo[comprimento:]

    return cabecalho_map, corpo[:comprimento], cabecalho_map.get("type", ""), restante

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(1)

    print(f"Servidor escutando em {SERVER_HOST}:{SERVER_PORT}")

    conn, addr = server.accept()
    print(f"Conexão de {addr}")

    # Extrai cenário do argumento
    cenario = sys.argv[1] if len(sys.argv) > 1 else "A"

    buffer_residual = b""

    cabecalhos, corpo, tipo, buffer_residual = ler_mensagem(conn, buffer_residual)

    if not cabecalhos:
        print("Falha ao receber mensagem inicial")
        conn.close()
        server.close()
        return

    auth = cabecalhos.get("x-custom-auth", "")
    print("Header recebido:", cabecalhos)

    if auth != EXPECTED_AUTH or tipo != "AUTH":
        print("Autenticação inválida")
        conn.close()
        server.close()
        return

    conn.sendall(b"AUTH-OK")

    inicio = time.time()
    total_bytes = 0

    with open(OUTPUT_FILE, "wb") as f:
        while True:
            cabecalhos, data, tipo, buffer_residual = ler_mensagem(conn, buffer_residual)

            if not cabecalhos:
                break

            auth = cabecalhos.get("x-custom-auth", "")
            if auth != EXPECTED_AUTH:
                print("Autenticação inválida em mensagem recebida")
                break

            if tipo == "FIN":
                conn.sendall(b"FIN-ACK")
                break

            f.write(data)
            total_bytes += len(data)

    fim = time.time()
    tempo_total = fim - inicio

    print(f"Tempo: {tempo_total:.4f}s")
    print(f"Bytes: {total_bytes}")
    print(f"Throughput: {total_bytes / tempo_total:.2f} B/s")

    conn.close()
    server.close()

if __name__ == "__main__":
    start_server()