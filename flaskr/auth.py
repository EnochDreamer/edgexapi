import json
from flask import request, abort, current_app
from functools import wraps
from jose import jwt
from jose import exceptions as jose_exceptions
from urllib.request import urlopen
import os


# my secrets , left here as this app isn't going to go to production
# Kinde domain / tenant (example: your-workspace.kinde.com)
KINDE_DOMAIN = os.getenv('KINDE_DOMAIN')
# Algorithms expected for JWT verification. Default to RS256; allow override via KINDE_ALGORITHMS="RS256,RS512"
_alg_env = os.getenv('KINDE_ALGORITHMS', 'RS256')
ALGORITHMS = [a.strip() for a in _alg_env.split(',') if a.strip()]
KINDE_API_AUDIENCE = os.getenv('KINDE_AUDIENCE')
KINDE_ISSUER = os.getenv('KINDE_ISSUER')
KINDE_JWKS_URL = os.getenv('KINDE_JWKS_URL')


# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header


# function to verify JWT


def get_token_auth_header():
    auth = request.headers.get('Authorization', None)
    if not auth:
        abort(401)

    # splits components on whitespace
    parts = auth.split()

    # validates token to be a bearer token
    if parts[0].lower() != 'bearer':
        abort(401)

    # validates token has two components
    if len(parts) != 2:
        abort(401)

    token = parts[1]
    return token




# checks for required permission


def check_permissions(permission, payload):
    if payload is None:
        abort(401)
    # Kinde tokens may include an empty permissions list; treat missing as empty
    perms = payload.get("permissions") or []
    if not isinstance(perms, list):
        # if permissions come as a space-delimited string, split them
        if isinstance(perms, str):
            perms = perms.split()
        else:
            perms = []
    if permission:
        if permission not in perms:
            abort(403)
    return True


# verifies JWT Source signature


def verify_decode_jwt(token, allow_signature_only: bool = False):
    # Get unverified header and claims first so we can derive issuer/jwks URL
    unverified_header = jwt.get_unverified_header(token)
    try:
        unverified_claims = jwt.get_unverified_claims(token)
    except Exception:
        unverified_claims = {}

    # Determine issuer base URL either from configured domain, token 'iss',
    # or fallbacks via KINDE_ISSUER / KINDE_JWKS_URL environment variables.
    issuer = None
    if KINDE_DOMAIN:
        issuer = 'https://' + KINDE_DOMAIN
    elif unverified_claims.get('iss'):
        issuer = unverified_claims.get('iss')
    elif KINDE_ISSUER:
        issuer = KINDE_ISSUER
    elif KINDE_JWKS_URL:
        # Derive issuer by stripping the well-known suffix if present
        issuer = KINDE_JWKS_URL
        if issuer.endswith('/.well-known/jwks.json'):
            issuer = issuer[: -len('/.well-known/jwks.json')]

    if not issuer:
        current_app.logger.warning('No issuer found (env KINDE_DOMAIN/KINDE_ISSUER/KINDE_JWKS_URL or token iss); token claims: %s', unverified_claims)
        raise AuthError({'code': 'invalid_issuer', 'description': 'Issuer not found'}, 401)

    jwks_url = issuer.rstrip('/') + '/.well-known/jwks.json'
    jsonurl = urlopen(jwks_url)
    jwks = json.loads(jsonurl.read())
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

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
            # Build decode arguments and options dynamically. Some tokens from
            # webhooks may omit iss/aud/exp; in that case we perform
            # signature-only verification (we still require a trusted JWKS).
            decode_kwargs = {'algorithms': ALGORITHMS}
            options = {'verify_aud': False}

            # Only include issuer validation if we derived an issuer
            if issuer:
                decode_kwargs['issuer'] = issuer.rstrip('/') + '/'
            else:
                # no issuer -> disable issuer verification
                options['verify_iss'] = False

            # If token lacks exp claim, disable expiry verification
            if 'exp' not in unverified_claims:
                options['verify_exp'] = False

            current_app.logger.debug('Verifying token with issuer=%s jwks_url=%s header=%s claims_preview=%s', issuer, jwks_url, unverified_header, {k: unverified_claims.get(k) for k in ('aud','iss','exp')})
            # Perform decode (signature verified using rsa_key). We disable
            # audience check because we handle aud lists manually below.
            payload = jwt.decode(token, rsa_key, options=options, **decode_kwargs)

            # Manual audience check (support aud as string or list)
            if KINDE_API_AUDIENCE:
                aud_claim = payload.get('aud')
                if aud_claim is None:
                    # Some tokens may use 'audience' key
                    aud_claim = payload.get('audience')

                if isinstance(aud_claim, list):
                    if KINDE_API_AUDIENCE not in aud_claim:
                        raise AuthError({
                            'code': 'invalid_audience',
                            'description': 'The required audience is not present in the token.'
                        }, 401)
                else:
                    if aud_claim != KINDE_API_AUDIENCE:
                        raise AuthError({
                            'code': 'invalid_audience',
                            'description': 'Incorrect audience. Please, check the audience.'
                        }, 401)

            return payload

        except jose_exceptions.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jose_exceptions.JWTClaimsError:
            # If allowed, attempt a relaxed signature-only decode (no iss/aud/exp checks)
            if allow_signature_only:
                current_app.logger.info('JWTClaimsError: attempting signature-only verification because allow_signature_only=True')
                try:
                    relaxed_options = {'verify_aud': False, 'verify_iss': False, 'verify_exp': False}
                    relaxed_payload = jwt.decode(token, rsa_key, options=relaxed_options, algorithms=ALGORITHMS)
                    # minimal structural checks: ensure type and data.user.id exist
                    if not (isinstance(relaxed_payload, dict) and relaxed_payload.get('type') and isinstance(relaxed_payload.get('data'), dict) and isinstance(relaxed_payload['data'].get('user'), dict) and relaxed_payload['data']['user'].get('id')):
                        raise AuthError({'code': 'invalid_payload', 'description': 'Required event payload missing'}, 401)
                    return relaxed_payload
                except Exception:
                    current_app.logger.exception('Relaxed signature-only verification failed')
                    raise AuthError({
                        'code': 'invalid_claims',
                        'description': 'Incorrect claims. Please, check the audience and issuer.'
                    }, 401)
            else:
                raise AuthError({
                    'code': 'invalid_claims',
                    'description': 'Incorrect claims. Please, check the audience and issuer.'
                }, 401)
        except jose_exceptions.JOSEError:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
        except Exception:
            # Fallback for unexpected errors
            current_app.logger.exception('Unexpected error verifying token')
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
        'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
    }, 400)



# Authentication decorator function


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_auth_header()
            except:
                abort(401)
            try:
                payload = verify_decode_jwt(token)
            except:
                abort(401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator