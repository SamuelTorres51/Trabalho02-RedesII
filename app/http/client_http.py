import sys

sys.path.insert(0, '/app')

from app.http.client_http_tcp import start_client as start_tcp_client
from app.http.client_http_rudp import start_client as start_rudp_client


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 app/http/client_http.py <tcp|rudp> [recurso]')
        sys.exit(1)

    modo = sys.argv[1].lower()
    recurso = sys.argv[2] if len(sys.argv) > 2 else '/'

    if modo == 'tcp':
        start_tcp_client(recurso)
    elif modo == 'rudp':
        start_rudp_client(recurso)
    else:
        print('Modo invalido. Use tcp ou rudp.')
        sys.exit(1)


if __name__ == '__main__':
    main()