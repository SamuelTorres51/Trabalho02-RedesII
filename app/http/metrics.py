import csv
import os
from pathlib import Path

from app.common.config import HTTP_LOG_DIR


def salvar_log_http(
    modo,
    cenario,
    recurso,
    tempo_dns,
    tempo_total,
    bytes_recebidos,
    status_http,
    sucesso=True,
):
    os.makedirs(HTTP_LOG_DIR, exist_ok=True)

    caminho = Path(HTTP_LOG_DIR) / f"http_{modo}_cenario_{cenario}.csv"
    arquivo_existe = caminho.is_file()
    throughput = bytes_recebidos / tempo_total if tempo_total > 0 else 0

    with caminho.open("a", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)

        if not arquivo_existe:
            writer.writerow([
                "cenario",
                "recurso",
                "tempo_dns",
                "tempo_total",
                "bytes",
                "throughput",
                "status_http",
                "sucesso",
            ])

        writer.writerow([
            cenario,
            recurso,
            round(tempo_dns, 4),
            round(tempo_total, 4),
            bytes_recebidos,
            round(throughput, 2),
            status_http,
            int(bool(sucesso)),
        ])

    return str(caminho)