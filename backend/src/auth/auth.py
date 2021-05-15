import json
from os import error, stat
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'hafez.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header


def get_token_auth_header():
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError(status_code= 401 , error="Authorization header is expected.")

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError(status_code= 401 , error="Authorization header must start with 'Bearer'")

    elif len(parts) == 1:
        raise AuthError(status_code= 401 , error="Token not found.")

    elif len(parts) > 2:
        raise AuthError(status_code= 401 , error="Authorization header must be bearer token.")

    token = parts[1]
    return token


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError(status_code=400,error="malformed token the permissions section is not available")
    
    if permission not in payload['permissions']:
        raise AuthError(status_code=401,error="unauthorized access , user doesnt have the required permissions")

    return True




def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError(status_code= 401 , error="Authorization malformed.")


    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError(status_code= 401 , error="Token expired.")


        except jwt.JWTClaimsError:
            raise AuthError(status_code= 401 , error="Incorrect claims. Please, check the audience and issuer.")

        except Exception:
            raise AuthError(status_code= 400 , error="Unable to parse authentication token.")


    raise AuthError(status_code= 400 , error="Unable to find the appropriate key.")



def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator