"""Add non_work_item_types and link package types to them

Replaces the hard-coded "Management Plan & Related Documents / Post Decision"
labels with database-driven configuration, and links phase-less package types
to the non-work bucket they belong to.

Revision ID: b8d2f4a6c1e3
Revises: a7c3e9f1b2d4
Create Date: 2026-11-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8d2f4a6c1e3'
down_revision = 'a7c3e9f1b2d4'
branch_labels = None
depends_on = None

NON_WORK_ITEM_TYPES = [
    {
        'code': 'MANAGEMENT_PLAN',
        'work_label': 'Management Plan & Related Documents',
        'phase_label': 'Post Decision',
        'eligibility': 'APPROVED_CONDITION',
        'is_onboarding_option': True,
        'sort_order': 1,
    },
]

# Phase-less package type name -> non-work item type code. Reports share the Management Plan
# bucket in the Documents table; the Submission Type filter tells them apart.
PACKAGE_TYPE_MAPPING = {
    'Management Plan': 'MANAGEMENT_PLAN',
    'IEM': 'MANAGEMENT_PLAN',
    'Report': 'MANAGEMENT_PLAN',
}


def upgrade():
    """Create and seed non_work_item_types, then link phase-less package types."""
    non_work_item_types = op.create_table(
        'non_work_item_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False,
                  comment='Matches the NonWorkItemType enum value, e.g. MANAGEMENT_PLAN'),
        sa.Column('work_label', sa.String(length=255), nullable=False,
                  comment='Text shown in the Work column/filter, e.g. Management Plan & Related Documents'),
        sa.Column('phase_label', sa.String(length=255), nullable=False,
                  comment='Text shown in the Phase column/filter, e.g. Post Decision'),
        sa.Column('eligibility', sa.String(length=50), nullable=False,
                  comment='NonWorkItemEligibility value deciding which projects this type applies to'),
        sa.Column('is_onboarding_option', sa.Boolean(), nullable=False, server_default=sa.false(),
                  comment='Whether this type is offered as a selectable entry when onboarding a proponent'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_date', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.Column('updated_by', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_non_work_item_types_code'),
    )
    op.bulk_insert(non_work_item_types, NON_WORK_ITEM_TYPES)

    with op.batch_alter_table('package_types', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'non_work_item_type_id', sa.Integer(), nullable=True,
            comment='Non-work bucket (e.g. Management Plan) packages of this type belong to '
                    'when not tied to a work'))
        batch_op.create_foreign_key(
            'fk_package_types_non_work_item_type_id', 'non_work_item_types',
            ['non_work_item_type_id'], ['id'])

    conn = op.get_bind()
    for package_type_name, code in PACKAGE_TYPE_MAPPING.items():
        conn.execute(
            sa.text(
                "UPDATE package_types SET non_work_item_type_id = "
                "(SELECT id FROM non_work_item_types WHERE code = :code) "
                "WHERE name = :name AND start_phase_id IS NULL AND end_phase_id IS NULL"
            ),
            {"code": code, "name": package_type_name},
        )


def downgrade():
    """Unlink package types and drop non_work_item_types."""
    with op.batch_alter_table('package_types', schema=None) as batch_op:
        batch_op.drop_constraint('fk_package_types_non_work_item_type_id', type_='foreignkey')
        batch_op.drop_column('non_work_item_type_id')
    op.drop_table('non_work_item_types')
