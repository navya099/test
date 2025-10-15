# app.py
from flask import Flask, send_from_directory
from flask_cors import CORS
from web.api_routes import api
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api, url_prefix="/api")

    @app.route("/")
    def index():
        return send_from_directory(os.path.dirname(__file__), "index.html")

    return app