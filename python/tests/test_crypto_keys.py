from dendro.api_helpers.services._crypto_keys import generate_keypair


def test_crypto_keys():
    public_key_hex, private_key_hex = generate_keypair() # this does checks internally
    assert public_key_hex
    assert private_key_hex
