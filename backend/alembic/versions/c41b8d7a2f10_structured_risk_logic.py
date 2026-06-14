"""Structured risk results, unassessed state, and risk history.

Revision ID: c41b8d7a2f10
Revises: bd0f7cf88e22
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c41b8d7a2f10"
down_revision: Union[str, None] = "bd0f7cf88e22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STRUCTURED_COLUMNS = (
    ("prediction_status", sa.String(), True),
    ("severity", sa.String(), True),
    ("predicted_class", sa.String(), True),
    ("probabilities", sa.JSON(), True),
    ("input_snapshot", sa.JSON(), True),
    ("input_provenance", sa.JSON(), True),
    ("oldest_input_age_days", sa.Integer(), True),
    (
        "has_stale_inputs",
        sa.Boolean(),
        False,
        sa.text("false"),
    ),
)


def _add_structured_columns(table: str) -> None:
    for definition in STRUCTURED_COLUMNS:
        name, column_type, nullable, *default = definition
        op.add_column(
            table,
            sa.Column(
                name,
                column_type,
                nullable=nullable,
                server_default=default[0] if default else None,
            ),
        )


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("gestation_in_previous_pregnancy", sa.Integer(), nullable=True),
    )
    op.alter_column(
        "patients",
        "risk_level",
        existing_type=sa.String(),
        server_default=sa.text("'unassessed'"),
        nullable=False,
    )

    for table in (
        "gdm_assessments",
        "anemia_assessments",
        "fetal_health_assessments",
        "maternal_health_assessments",
    ):
        _add_structured_columns(table)

    op.create_table(
        "patient_risk_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("assessment_type", sa.String(), nullable=True),
        sa.Column("model_severities", sa.JSON(), nullable=True),
        sa.Column("assessed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"]),
    )
    op.create_index(
        "ix_patient_risk_history_patient_id",
        "patient_risk_history",
        ["patient_id"],
    )
    op.create_index(
        "ix_patient_risk_history_visit_id",
        "patient_risk_history",
        ["visit_id"],
    )
    op.create_index(
        "ix_patient_risk_history_risk_level",
        "patient_risk_history",
        ["risk_level"],
    )
    op.create_index(
        "ix_patient_risk_history_assessed_at",
        "patient_risk_history",
        ["assessed_at"],
    )

    op.execute(
        """
        UPDATE gdm_assessments
        SET prediction_status = 'completed',
            severity = CASE risk_level
                WHEN 0 THEN 'low'
                WHEN 1 THEN 'medium'
                WHEN 2 THEN 'high'
            END,
            predicted_class = CASE risk_level
                WHEN 0 THEN 'negative'
                WHEN 1 THEN 'elevated'
                WHEN 2 THEN 'positive'
            END
        WHERE ai_report IS NOT NULL AND risk_level IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE anemia_assessments
        SET prediction_status = 'completed',
            severity = CASE
                WHEN lower(trim(diagnosis)) = 'healthy' THEN 'low'
                ELSE 'high'
            END,
            predicted_class = diagnosis
        WHERE ai_report IS NOT NULL AND diagnosis IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE fetal_health_assessments
        SET prediction_status = 'completed',
            severity = CASE status
                WHEN 1 THEN 'low'
                WHEN 2 THEN 'medium'
                WHEN 3 THEN 'high'
            END,
            predicted_class = CASE status
                WHEN 1 THEN 'Normal'
                WHEN 2 THEN 'Suspect'
                WHEN 3 THEN 'Pathological'
            END
        WHERE ai_report IS NOT NULL AND status IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE maternal_health_assessments
        SET prediction_status = 'completed',
            severity = CASE risk_level
                WHEN 0 THEN 'low'
                WHEN 1 THEN 'medium'
                WHEN 2 THEN 'high'
            END,
            predicted_class = CASE risk_level
                WHEN 0 THEN 'Low Risk'
                WHEN 1 THEN 'Mid Risk'
                WHEN 2 THEN 'High Risk'
            END
        WHERE ai_report IS NOT NULL AND risk_level IS NOT NULL
        """
    )

    op.execute(
        """
        WITH model_results AS (
            SELECT v.patient_id, 'gdm' AS model, a.severity, a.created_at
            FROM gdm_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
            UNION ALL
            SELECT v.patient_id, 'anemia', a.severity, a.created_at
            FROM anemia_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
            UNION ALL
            SELECT v.patient_id, 'fetal', a.severity, a.created_at
            FROM fetal_health_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
            UNION ALL
            SELECT v.patient_id, 'preeclampsia', a.severity, a.created_at
            FROM maternal_health_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
        ),
        ranked AS (
            SELECT *,
                   row_number() OVER (
                       PARTITION BY patient_id, model
                       ORDER BY created_at DESC
                   ) AS position
            FROM model_results
            WHERE severity IS NOT NULL
        ),
        patient_risk AS (
            SELECT patient_id,
                   max(CASE severity
                       WHEN 'high' THEN 2
                       WHEN 'medium' THEN 1
                       WHEN 'low' THEN 0
                   END) AS risk_rank
            FROM ranked
            WHERE position = 1
            GROUP BY patient_id
        )
        UPDATE patients p
        SET risk_level = CASE patient_risk.risk_rank
            WHEN 2 THEN 'high'
            WHEN 1 THEN 'medium'
            WHEN 0 THEN 'low'
            ELSE 'unassessed'
        END
        FROM patient_risk
        WHERE p.id = patient_risk.patient_id
        """
    )
    op.execute(
        """
        UPDATE patients p
        SET risk_level = 'unassessed'
        WHERE NOT EXISTS (
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
              AND (g.id IS NOT NULL OR a.id IS NOT NULL
                   OR f.id IS NOT NULL OR m.id IS NOT NULL)
        )
        """
    )
    op.execute(
        """
        INSERT INTO patient_risk_history (
            patient_id, risk_level, assessment_type, assessed_at
        )
        SELECT p.id, p.risk_level, 'backfill', max(result_time)
        FROM patients p
        JOIN (
            SELECT v.patient_id, a.created_at AS result_time
            FROM gdm_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
            UNION ALL
            SELECT v.patient_id, a.created_at
            FROM anemia_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
            UNION ALL
            SELECT v.patient_id, a.created_at
            FROM fetal_health_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
            UNION ALL
            SELECT v.patient_id, a.created_at
            FROM maternal_health_assessments a JOIN visits v ON v.id = a.visit_id
            WHERE a.prediction_status = 'completed'
        ) results ON results.patient_id = p.id
        WHERE p.risk_level <> 'unassessed'
        GROUP BY p.id, p.risk_level
        """
    )


def downgrade() -> None:
    op.drop_index("ix_patient_risk_history_assessed_at", table_name="patient_risk_history")
    op.drop_index("ix_patient_risk_history_risk_level", table_name="patient_risk_history")
    op.drop_index("ix_patient_risk_history_visit_id", table_name="patient_risk_history")
    op.drop_index("ix_patient_risk_history_patient_id", table_name="patient_risk_history")
    op.drop_table("patient_risk_history")

    for table in (
        "maternal_health_assessments",
        "fetal_health_assessments",
        "anemia_assessments",
        "gdm_assessments",
    ):
        for definition in reversed(STRUCTURED_COLUMNS):
            op.drop_column(table, definition[0])

    op.alter_column(
        "patients",
        "risk_level",
        existing_type=sa.String(),
        server_default=sa.text("'low'"),
        nullable=False,
    )
    op.drop_column("patients", "gestation_in_previous_pregnancy")
