import os

import yaml
from flasgger import Swagger
from flask import Flask
from flask_migrate import Migrate
from sqlalchemy import text

from .error_handler import error_handlers
from .logger import init_logger
from .db.models import db
from .api import register_apis

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_object("app.config.Config")
    else:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    Migrate(app, db)

    register_apis(app)
    error_handlers(app)
    init_logger(app)

    with open("docs/api/swagger.yaml") as f:
        template = yaml.safe_load(f)
    Swagger(app, template=template)

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok"}, 200
        except Exception:
            return {"status": "error"}, 500

    return app
