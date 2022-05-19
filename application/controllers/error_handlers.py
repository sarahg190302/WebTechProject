from flask import Flask, request
from flask import render_template, make_response, jsonify
from flask import current_app as app
from application.models import *
from jsonschema import ValidationError

@app.errorhandler(404)
def not_found_error(e):
    return 'Page not found', 404

@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description, ValidationError):
        original_error = error.description
        return make_response(jsonify({'error': original_error.message}), 400)
    # handle other "Bad Request"-errors
    return error