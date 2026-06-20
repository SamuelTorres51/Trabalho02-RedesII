def montar_mensagem_dns(query_id, nome, ip=""):
    linhas = [
        f"ID:{query_id}",
        f"NAME:{nome}",
        f"IP:{ip}",
    ]
    return ("\n".join(linhas) + "\n\n").encode()


def ler_mensagem_dns(payload):
    texto = payload.decode(errors="replace")
    cabecalho = texto.split("\n\n", 1)[0]

    campos = {}
    for linha in cabecalho.splitlines():
        if ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        campos[chave.strip().upper()] = valor.strip()

    query_id = campos.get("ID", "")
    nome = campos.get("NAME", "")
    ip = campos.get("IP", "")

    return query_id, nome, ip