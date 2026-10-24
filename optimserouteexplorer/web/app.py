# web/app.py
"""Flask 앱 팩토리."""
import logging
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from web.api_routes import api

logger = logging.getLogger(__name__)


def create_app(config: dict | None = None) -> Flask:
    """앱 팩토리. config 로 테스트/배포 설정 주입."""
    app = Flask(__name__)

    # 기본 설정 (환경변수 우선)
    app.config.update(
        CORS_ORIGINS=os.environ.get(
            "CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000"
        ).split(","),
        JSON_AS_ASCII=False,
    )
    if config:
        app.config.update(config)

    # CORS: /api/* 만, 오리진 제한
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
    )

    app.register_blueprint(api, url_prefix="/api")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    @app.route("/")
    def index():
        return send_from_directory(base_dir, "index.html")

    # 정적 리소스 + SPA fallback
    @app.route("/<path:path>")
    def static_or_spa(path: str):
        # API 경로는 SPA fallback 제외
        if path == "api" or path.startswith("api/"):
            from flask import abort
            abort(404)

        full = os.path.join(base_dir, path)
        if os.path.isfile(full):
            return send_from_directory(base_dir, path)
        return send_from_directory(base_dir, "index.html")

    # API 404 → JSON
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify(error="not_found"), 404
        return e

    # API 500 → JSON
    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith("/api/"):
            logger.exception("서버 오류: %s", e)
            return jsonify(error="internal_error"), 500
        return e

    return app