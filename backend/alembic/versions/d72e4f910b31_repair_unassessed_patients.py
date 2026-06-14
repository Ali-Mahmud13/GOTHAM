"""Repair patients incorrectly left as low risk without an assessment.

Revision ID: d72e4f910b31
Revises: c41b8d7a2f10
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op

revision: str = "d72e4f910b31"
down_revision: Union[str, None] = "c41b8d7a2f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE patients p
        SET risk_level = 'unassessed'
        WHERE p.risk_level = 'low'
          AND NOT EXISTS (
              SELECT 1
              FROM visits v
              LEFT JOIN gdm_assessments g
                ON g.visit_id = v.id AND g.prediction_status = 'completed'
              LEFT JOIN anemia_assessments a
                ON a.visit_id = v.id AND a.prediction_status = 'completed'
              LEFT JOIN fetal_health_assessments f
                ON f.visit_id = v.id AND f.prediction_status = 'completed'
              LEFT JOIN maternal_health_assessments m
                ON m.visit_id = v.id AND m.prediction_status = 'completed'
              WHERE v.patient_id = p.id
                AND (
                    g.id IS NOT NULL OR a.id IS NOT NULL
                    OR f.id IS NOT NULL OR m.id IS NOT NULL
                )
          )
        """
    )


def downgrade() -> None:
    # The previous low-risk value cannot be distinguished from a genuine
    # completed low-risk assessment, so this data repair is intentionally kept.
    pass
