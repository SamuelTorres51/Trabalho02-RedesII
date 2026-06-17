import struct
import zlib

HEADER_FORMAT = "!IIII"  # seq_num, tamanho, checksum, auth_len
HEADER_SIZE = 16  # 4 bytes * 4 campos

def calcular_checksum(data):
    return zlib.crc32(data)

def criar_pacote(seq_num, dados, auth_hash=""):
    """
    Cria um pacote com header, autenticação e dados.
    
    Estrutura:
    - seq_num (4 bytes)
    - tamanho (4 bytes)
    - checksum (4 bytes)
    - auth_len (4 bytes)
    - auth_hash (variável)
    - dados (variável)
    """
    tamanho = len(dados)
    checksum = calcular_checksum(dados)
    auth_bytes = auth_hash.encode() if isinstance(auth_hash, str) else auth_hash
    auth_len = len(auth_bytes)

    header = struct.pack(
        HEADER_FORMAT,
        seq_num,
        tamanho,
        checksum,
        auth_len
    )

    return header + auth_bytes + dados

def ler_pacote(packet):
    """
    Lê um pacote e extrai seq_num, tamanho, checksum, auth_hash e dados.
    """
    header = packet[:HEADER_SIZE]
    
    seq_num, tamanho, checksum, auth_len = struct.unpack(
        HEADER_FORMAT,
        header
    )

    auth_hash = packet[HEADER_SIZE:HEADER_SIZE + auth_len].decode()
    dados = packet[HEADER_SIZE + auth_len:]

    return seq_num, tamanho, checksum, auth_hash, dados