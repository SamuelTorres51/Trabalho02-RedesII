import hashlib

def gerar_auth(matricula, nome):
    texto = f"{matricula}{nome}"
    return hashlib.sha256(texto.encode()).hexdigest()