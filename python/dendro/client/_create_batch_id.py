import random


def create_batch_id() -> str:
    """Create a new batch ID string.

    This is a random string that can be used when submitting multiple jobs.
    """
    choices = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choices(choices, k=8))
