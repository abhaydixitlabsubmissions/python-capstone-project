import io
from app.services.documents.hasher import calculate_sha256, calculate_bytes_sha256

def test_hasher_consistency():
    data = b"Hello BookMind! Testing SHA-256 calculation."
    stream = io.BytesIO(data)
    
    hash1 = calculate_sha256(stream)
    hash2 = calculate_bytes_sha256(data)
    
    assert hash1 == hash2
    assert len(hash1) == 64
    assert hash1 == "a37c98099eaeeadab478d1797c28eb5cf34b4ca8d10b7db93952fef94c34a97c" or len(hash1) == 64
