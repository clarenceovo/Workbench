#write function to craete uuid

import uuid

def get_uuid(length:int=16) -> str:
    """
    Generate a new UUID (Universally Unique Identifier).

    :return: A string representation of the UUID.
    """
    return str(uuid.uuid4()).replace("-", "")[:length]  # Return the first 16 characters of the UUID

if __name__ == "__main__":
    # Example usage

    print(get_uuid())