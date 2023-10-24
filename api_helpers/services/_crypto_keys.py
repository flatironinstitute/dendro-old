def sign_message(msg: dict, public_key_hex: str, private_key_hex: str) -> str:
    return _sign_message(msg, public_key_hex, private_key_hex)

ed25519PubKeyPrefix = "302a300506032b6570032100"
ed25519PrivateKeyPrefix = "302e020100300506032b657004220420"

def _deterministic_json_dumps(x: dict):
    import simplejson
    return simplejson.dumps(x, separators=(',', ':'), indent=None, allow_nan=False, sort_keys=True)

def _sha1_of_string(txt: str) -> str:
    import hashlib
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret = hh.hexdigest()
    return ret

def _sign_message(msg: dict, public_key_hex: str, private_key_hex: str) -> str:
    msg_json = _deterministic_json_dumps(msg)
    return _sign_message_str(msg_json, public_key_hex, private_key_hex)


def _sign_message_str(msg: str, public_key_hex: str, private_key_hex: str) -> str:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    msg_hash = _sha1_of_string(msg)
    msg_bytes = bytes.fromhex(msg_hash)
    privk = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
    pubk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
    signature = privk.sign(msg_bytes).hex()
    pubk.verify(bytes.fromhex(signature), msg_bytes)
    return signature

def _verify_signature(msg: dict, public_key_hex: str, signature: str):
    msg_json = _deterministic_json_dumps(msg)
    return _verify_signature_str(msg_json, public_key_hex, signature)

def _verify_signature_str(msg: str, public_key_hex: str, signature: str):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    msg_hash = _sha1_of_string(msg)
    msg_bytes = bytes.fromhex(msg_hash)
    pubk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
    try:
        pubk.verify(bytes.fromhex(signature), msg_bytes)
    except: # noqa: E722
        return False
    return True

def generate_keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    privk = Ed25519PrivateKey.generate()
    pubk = privk.public_key()
    private_key_hex = privk.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    ).hex() # type: ignore
    public_key_hex = pubk.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    ).hex() # type: ignore
    test_msg = {'a': 1}
    test_signature = _sign_message(test_msg, public_key_hex, private_key_hex)
    assert _verify_signature(test_msg, public_key_hex, test_signature)
    return public_key_hex, private_key_hex
