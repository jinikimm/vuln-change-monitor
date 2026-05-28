from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from uuid import uuid4

db = SQLAlchemy()

class VulnerabilitySnapshot(db.Model):
    __tablename__ = "vulnerability_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))

    product_name = db.Column(db.String(128), nullable=False)
    product_version = db.Column(db.String(64), nullable=False)
    source = db.Column(db.String(128), nullable=False)

    snapshot_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    previous_snapshot_id = db.Column(db.String(36), db.ForeignKey("vulnerability_snapshots.id"), nullable=True)
    
    finding_count = db.Column(db.Integer, nullable=False)
    
    summary_new = db.Column(db.Integer, nullable=False)
    summary_resolved = db.Column(db.Integer, nullable=False)
    summary_severity_changed = db.Column(db.Integer, nullable=False)
    summary_status_changed = db.Column(db.Integer, nullable=False)
    summary_unchanged = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("product_name", "product_version", "source", "snapshot_time", name="uq_vuln_snapshot"),
    )

class VulnerabilityFinding(db.Model):
    __tablename__ = "vulnerability_findings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    snapshot_id = db.Column(db.String(36), db.ForeignKey("vulnerability_snapshots.id"), nullable=False, index=True)
    
    vulnerability_id = db.Column(db.String(64), nullable=False)
    component_name = db.Column(db.String(128), nullable=False)
    component_version = db.Column(db.String(64), nullable=False)
    package_url = db.Column(db.String(255), nullable=True)
    
    severity = db.Column(db.String(16), nullable=False)
    cvss_score = db.Column(db.Float, nullable=False)
    affected_status = db.Column(db.String(32), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("snapshot_id", "vulnerability_id", "component_name", "component_version", name="uq_vuln_finding"),
    )

class VulnerabilityChange(db.Model):
    __tablename__ = "vulnerability_changes"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    snapshot_id = db.Column(db.String(36), db.ForeignKey("vulnerability_snapshots.id"), nullable=False, index=True) 
    previous_snapshot_id = db.Column(db.String(36), db.ForeignKey("vulnerability_snapshots.id"), nullable=True) 
    
    change_type = db.Column(db.String(32), nullable=False)
    
    vulnerability_id = db.Column(db.String(64), nullable=True)
    component_name = db.Column(db.String(128), nullable=True)
    component_version = db.Column(db.String(64), nullable=True)
    package_url = db.Column(db.String(255), nullable=True)
    
    previous_severity = db.Column(db.String(16), nullable=True)
    current_severity = db.Column(db.String(16), nullable=True)
    
    previous_cvss_score = db.Column(db.Float, nullable=True)
    current_cvss_score = db.Column(db.Float, nullable=True)
    
    previous_affected_status = db.Column(db.String(32), nullable=True)
    current_affected_status = db.Column(db.String(32), nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
