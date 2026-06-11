from datetime import datetime, timezone
from uuid import uuid4

from flask_sqlalchemy import SQLAlchemy


SEVERITY_ENUM = ("low", "medium", "high", "critical", "none", "unknown")
STATUS_ENUM = (
    "affected",
    "not affected",
    "fixed",
    "under_investigation",
    "accepted_risk",
)


db = SQLAlchemy()


class VulnerabilitySnapshot(db.Model):
    __tablename__ = "vulnerability_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))

    product_name = db.Column(db.String(128), nullable=False, index=True)
    product_version = db.Column(db.String(64), nullable=False, index=True)
    source = db.Column(db.String(128), nullable=False, index=True)

    snapshot_time = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    previous_snapshot_id = db.Column(
        db.String(36), db.ForeignKey("vulnerability_snapshots.id"), nullable=True
    )

    finding_count = db.Column(db.Integer, nullable=False)

    summary_new = db.Column(db.Integer, nullable=False)
    summary_resolved = db.Column(db.Integer, nullable=False)
    summary_severity_changed = db.Column(db.Integer, nullable=False)
    summary_status_changed = db.Column(db.Integer, nullable=False)
    summary_unchanged = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "product_name",
            "product_version",
            "source",
            "snapshot_time",
            name="uq_vuln_snapshot",
        ),
        db.CheckConstraint("finding_count >= 0", name="check_finding_count_positive"),
        db.CheckConstraint("summary_new >= 0", name="check_summary_new_positive"),
        db.CheckConstraint("summary_resolved >= 0", name="check_summary_resolved_positive"),
        db.CheckConstraint("summary_severity_changed >= 0", name="check_summary_severity_changed_positive"),
        db.CheckConstraint("summary_status_changed >= 0", name="check_summary_status_changed_positive"),
        db.CheckConstraint("summary_unchanged >= 0", name="check_summary_unchanged_positive"),
    )


class VulnerabilityFinding(db.Model):
    __tablename__ = "vulnerability_findings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    snapshot_id = db.Column(
        db.String(36),
        db.ForeignKey("vulnerability_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    vulnerability_id = db.Column(db.String(64), nullable=False)
    component_name = db.Column(db.String(128), nullable=False)
    component_version = db.Column(db.String(64), nullable=False)
    package_url = db.Column(db.String(255), nullable=True)

    severity = db.Column(db.Enum(*SEVERITY_ENUM, name="severity_enum"), nullable=False)
    cvss_score = db.Column(db.Float, nullable=False)
    epss_score = db.Column(db.Float, nullable=True)
    known_exploited = db.Column(db.Boolean, nullable=True)
    affected_status = db.Column(db.Enum(*STATUS_ENUM, name="status_enum"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "snapshot_id",
            "vulnerability_id",
            "component_name",
            "component_version",
            name="uq_vuln_finding",
        ),
    )


class VulnerabilityChange(db.Model):
    __tablename__ = "vulnerability_changes"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    snapshot_id = db.Column(
        db.String(36),
        db.ForeignKey("vulnerability_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_snapshot_id = db.Column(
        db.String(36), db.ForeignKey("vulnerability_snapshots.id", ondelete="CASCADE"), nullable=True
    )

    change_type = db.Column(db.String(32), nullable=False)

    vulnerability_id = db.Column(db.String(64), nullable=True)
    component_name = db.Column(db.String(128), nullable=True)
    component_version = db.Column(db.String(64), nullable=True)
    package_url = db.Column(db.String(255), nullable=True)

    previous_severity = db.Column(db.Enum(*SEVERITY_ENUM, name="severity_enum"), nullable=True)
    current_severity = db.Column(db.Enum(*SEVERITY_ENUM, name="severity_enum"), nullable=True)

    previous_cvss_score = db.Column(db.Float, nullable=True)
    current_cvss_score = db.Column(db.Float, nullable=True)

    previous_affected_status = db.Column(db.Enum(*STATUS_ENUM, name="status_enum"), nullable=True)
    current_affected_status = db.Column(db.Enum(*STATUS_ENUM, name="status_enum"), nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
