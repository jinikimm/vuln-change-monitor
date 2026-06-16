from alembic import op
import sqlalchemy as sa

revision = '4320614d2303'
down_revision = '4886206438e7'
branch_labels = None
depends_on = None

severity_enum = sa.Enum(
    "low", "medium", "high", "critical", "none", "unknown",
    name="severity_enum"
)

status_enum = sa.Enum(
    "affected", "not affected", "fixed", "under_investigation", "accepted_risk",
    name="status_enum"
)


def upgrade():
    bind = op.get_bind()

    severity_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    with op.batch_alter_table('vulnerability_changes') as batch_op:
        batch_op.alter_column(
            'previous_severity',
            existing_type=sa.VARCHAR(length=16),
            type_=severity_enum,
            existing_nullable=True,
            postgresql_using="previous_severity::severity_enum"
        )
        batch_op.alter_column(
            'current_severity',
            existing_type=sa.VARCHAR(length=16),
            type_=severity_enum,
            existing_nullable=True,
            postgresql_using="current_severity::severity_enum"
        )
        batch_op.alter_column(
            'previous_affected_status',
            existing_type=sa.VARCHAR(length=32),
            type_=status_enum,
            existing_nullable=True,
            postgresql_using="previous_affected_status::status_enum"
        )
        batch_op.alter_column(
            'current_affected_status',
            existing_type=sa.VARCHAR(length=32),
            type_=status_enum,
            existing_nullable=True,
            postgresql_using="current_affected_status::status_enum"
        )

        batch_op.drop_constraint(
            batch_op.f('vulnerability_changes_previous_snapshot_id_fkey'),
            type_='foreignkey'
        )
        batch_op.drop_constraint(
            batch_op.f('vulnerability_changes_snapshot_id_fkey'),
            type_='foreignkey'
        )

        batch_op.create_foreign_key(
            None, 'vulnerability_snapshots',
            ['snapshot_id'], ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            None, 'vulnerability_snapshots',
            ['previous_snapshot_id'], ['id'],
            ondelete='CASCADE'
        )

    with op.batch_alter_table('vulnerability_findings') as batch_op:
        batch_op.alter_column(
            'severity',
            existing_type=sa.VARCHAR(length=16),
            type_=severity_enum,
            existing_nullable=False,
            postgresql_using="severity::severity_enum"
        )
        batch_op.alter_column(
            'affected_status',
            existing_type=sa.VARCHAR(length=32),
            type_=status_enum,
            existing_nullable=False,
            postgresql_using="affected_status::status_enum"
        )

        batch_op.drop_constraint(
            batch_op.f('vulnerability_findings_snapshot_id_fkey'),
            type_='foreignkey'
        )
        batch_op.create_foreign_key(
            None, 'vulnerability_snapshots',
            ['snapshot_id'], ['id'],
            ondelete='CASCADE'
        )

    with op.batch_alter_table('vulnerability_snapshots') as batch_op:
        batch_op.create_index(None, ['product_name'])
        batch_op.create_index(None, ['product_version'])
        batch_op.create_index(None, ['snapshot_time'])
        batch_op.create_index(None, ['source'])


def downgrade():
    bind = op.get_bind()

    with op.batch_alter_table('vulnerability_snapshots') as batch_op:
        batch_op.drop_index(None)
        batch_op.drop_index(None)
        batch_op.drop_index(None)
        batch_op.drop_index(None)

    with op.batch_alter_table('vulnerability_findings') as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(
            batch_op.f('vulnerability_findings_snapshot_id_fkey'),
            'vulnerability_snapshots',
            ['snapshot_id'], ['id']
        )

        batch_op.alter_column(
            'affected_status',
            existing_type=status_enum,
            type_=sa.VARCHAR(length=32),
            existing_nullable=False
        )
        batch_op.alter_column(
            'severity',
            existing_type=severity_enum,
            type_=sa.VARCHAR(length=16),
            existing_nullable=False
        )

    with op.batch_alter_table('vulnerability_changes') as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

        batch_op.create_foreign_key(
            batch_op.f('vulnerability_changes_snapshot_id_fkey'),
            'vulnerability_snapshots',
            ['snapshot_id'], ['id']
        )
        batch_op.create_foreign_key(
            batch_op.f('vulnerability_changes_previous_snapshot_id_fkey'),
            'vulnerability_snapshots',
            ['previous_snapshot_id'], ['id']
        )

        batch_op.alter_column(
            'current_affected_status',
            existing_type=status_enum,
            type_=sa.VARCHAR(length=32),
            existing_nullable=True
        )
        batch_op.alter_column(
            'previous_affected_status',
            existing_type=status_enum,
            type_=sa.VARCHAR(length=32),
            existing_nullable=True
        )
        batch_op.alter_column(
            'current_severity',
            existing_type=severity_enum,
            type_=sa.VARCHAR(length=16),
            existing_nullable=True
        )
        batch_op.alter_column(
            'previous_severity',
            existing_type=severity_enum,
            type_=sa.VARCHAR(length=16),
            existing_nullable=True
        )

    status_enum.drop(bind, checkfirst=True)
    severity_enum.drop(bind, checkfirst=True)