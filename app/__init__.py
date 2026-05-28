import os
from flask import Flask
from flask_migrate import Migrate
from .error_handler import error_handlers
from .models import db
from .vulnerability_api import vulnerability_bp

def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)

	if test_config is None:
		app.config.from_object("app.config.Config")
	else:
		app.config.update(test_config)

	os.makedirs(app.instance_path, exist_ok=True)

	db.init_app(app)
	Migrate(app, db)

	app.register_blueprint(vulnerability_bp)
	error_handlers(app)

	@app.get("/healthz")
	def healthz():
		return {"status": "ok"}, 200

	return app