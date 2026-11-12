import hashlib
import base64
import os

def hash_payload(data: dict) -> str:
    """Gera um hash SHA256 do payload para integridade."""
    serialized = str(data).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()

def obfuscate_string(s: str) -> str:
    """
    Ofusca uma string simples para evitar detecção por strings visíveis no binário.
    (Uso educacional)
    """
    return base64.b64encode(s.encode()).decode()

def get_temp_dir() -> str:
    """Retorna o diretório temporário do sistema."""
    return os.environ.get('TEMP', os.environ.get('TMP', '/tmp'))