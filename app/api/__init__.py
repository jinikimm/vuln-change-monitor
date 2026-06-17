from flask import Blueprint
from .vulnerability_api import VulnerabilityAPIs
from ..service.vulnerability_service import VulnerabilityService


def register_apis(app):
    vuln_bp = Blueprint("vulnerability", __name__)
    vuln_service = VulnerabilityService()
    vuln_apis = VulnerabilityAPIs(vuln_service)
    vuln_apis.add_url_rules(vuln_bp)
    app.register_blueprint(vuln_bp)