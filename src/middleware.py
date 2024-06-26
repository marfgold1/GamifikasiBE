from functools import wraps
from flask import request


def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'X-API-KEY' not in request.headers:
            return {'message': 'API key is required'}, 401
        api_key = request.headers['X-API-KEY']
        if api_key != 'my_secret_key':
            return {'message': 'Invalid API key'}, 401
        return f(*args, **kwargs)
    return decorated
