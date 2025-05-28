#write function to craete uuid
import gzip
import json
import uuid
import hashlib
import hmac
import base64
import urllib.parse
import time
from io import BytesIO


def get_uuid(length:int=16) -> str:
    """
    Generate a new UUID (Universally Unique Identifier).

    :return: A string representation of the UUID.
    """
    return str(uuid.uuid4()).replace("-", "")[:length]  # Return the first 16 characters of the UUID


def get_htx_signature(api_key, api_secret, method, base_url, request_path, params,is_ws: bool = False) -> dict:
    """
    Generate a unique signature for HTX (Huobi Token Exchange).

    :return: A string representation of the HTX signature.
    """

    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
    params.update({
        'AccessKeyId': api_key,
        'SignatureMethod': 'HmacSHA256',
        'SignatureVersion': '2',
        'Timestamp': timestamp
    })
    sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = '\n'.join([method, base_url, request_path, encode_params])
    digest = hmac.new(api_secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()
    params['Signature'] = signature
    if is_ws:
        params['op'] = 'auth'
        params['type'] = 'api'
    return params

def decode_gzip_message(message: bytes) -> dict:
    buf = BytesIO(message)
    with gzip.GzipFile(fileobj=buf) as f:
        decoded_bytes = f.read()
    return json.loads(decoded_bytes.decode('utf-8'))


if __name__ == "__main__":
    # Example usage

    print(get_uuid())