from flask import Flask

from app.api.errors import ApiError, error_response
from app.api.alerts import bp as alerts_bp
from app.api.health import bp as health_bp
from app.api.products import bp as products_bp
from app.db.core import make_db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["db"] = make_db()
    app.register_blueprint(health_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(alerts_bp)

    @app.errorhandler(ApiError)
    def _handle_api_error(err: ApiError):
        return error_response(err)

    return app

