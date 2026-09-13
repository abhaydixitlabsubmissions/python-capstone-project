import hashlib
from typing import BinaryIO

def calculate_sha256(file_obj: BinaryIO) -> str:
    """Compute SHA-256 hash of a file stream without loading the entire file into memory."""
    sha256_hash = hashlib.sha256()
    file_obj.seek(0)
    for byte_block in iter(lambda: file_obj.read(65536), b""):
        sha256_hash.update(byte_block)
    file_obj.seek(0)
    return sha256_hash.hexdigest()

def calculate_bytes_sha256(data: bytes) -> str:
    """Compute SHA-256 hash directly from bytes."""
    return hashlib.sha256(data).hexdigest()
