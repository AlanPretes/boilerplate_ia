from functools import wraps

from flask import request
from flask import jsonify
from flask_basicauth import BasicAuth

from src.configs.settings import Settings


basic_auth = BasicAuth()

def token_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        token = request.headers.get("Authorization")
        
        if not token:
            return jsonify({"detail": "Token missing"}), 401
        
        if token != Settings.AUTH_TOKEN:
            return jsonify({"detail": "Token invalid"}), 401

        return fn(*args, **kwargs)
    
    return inner