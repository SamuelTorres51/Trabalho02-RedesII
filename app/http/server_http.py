import sys
from multiprocessing import Process

sys.path.insert(0, '/app')

from app.http.server_http_tcp import start_server as start_tcp_server
from app.http.server_http_rudp import start_server as start_rudp_server


def main():
    processo_tcp = Process(target=start_tcp_server)
    processo_rudp = Process(target=start_rudp_server)

    processo_tcp.start()
    processo_rudp.start()

    processo_tcp.join()
    processo_rudp.join()


if __name__ == '__main__':
    main()