import uuid


def _create_random_id(length: int) -> str:
    # Generate a random UUID
    full_uuid = uuid.uuid4()

    # Convert to a string and take the first [length] characters
    short_id = str(full_uuid).replace('-', '')[:length]

    return short_id
