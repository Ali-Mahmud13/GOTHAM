"""Repair appointment lifecycle, UTC storage, and token revocation.

Revision ID: e84f2b19a630
Revises: d72e4f910b31
Create Date: 2026-06-14
"""

from datetime import datetime, timezone
from typing import Sequence, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from alembic import context, op
import sqlalchemy as sa

revision: str = "e84f2b19a630"
down_revision: Union[str, None] = "d72e4f910b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _utc_naive(date_text: str, time_text: str, timezone_name: str) -> datetime | None:
    try:
        zone = ZoneInfo(timezone_name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    try:
        local = datetime.strptime(
            f"{date_text} {time_text}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=zone)
    except (TypeError, ValueError):
        return None
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    op.add_column(
        "auth_users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "appointments",
        sa.Column(
            "schedule_timezone",
            sa.String(),
            nullable=False,
            server_default=sa.text("'UTC'"),
        ),
    )
    op.add_column("appointments", sa.Column("start_at_utc", sa.DateTime(), nullable=True))
    op.add_column("appointments", sa.Column("end_at_utc", sa.DateTime(), nullable=True))
    op.add_column("appointments", sa.Column("cancellation_reason", sa.String(), nullable=True))
    op.add_column("appointments", sa.Column("outcome_recorded_at", sa.DateTime(), nullable=True))
    op.add_column("appointments", sa.Column("outcome_recorded_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_appointments_outcome_recorded_by",
        "appointments",
        "auth_users",
        ["outcome_recorded_by"],
        ["id"],
    )
    op.create_index("ix_appointments_start_at_utc", "appointments", ["start_at_utc"])
    op.create_index("ix_appointments_end_at_utc", "appointments", ["end_at_utc"])

    if context.is_offline_mode():
        op.execute(
            """
            UPDATE appointments
            SET schedule_timezone = COALESCE(NULLIF(timezone, ''), 'UTC'),
                start_at_utc = (
                    (appointment_date || ' ' || start_time)::timestamp
                    AT TIME ZONE COALESCE(NULLIF(timezone, ''), 'UTC')
                ),
                end_at_utc = (
                    (appointment_date || ' ' || end_time)::timestamp
                    AT TIME ZONE COALESCE(NULLIF(timezone, ''), 'UTC')
                )
            """
        )
        op.execute(
            """
            UPDATE appointments
            SET status = CASE
                    WHEN status = 'booked' THEN 'awaiting_outcome'
                    ELSE 'cancelled'
                END,
                cancellation_reason = CASE
                    WHEN status = 'pending_approval'
                    THEN 'registration_request_expired'
                    ELSE cancellation_reason
                END
            WHERE end_at_utc <= CURRENT_TIMESTAMP
              AND status IN ('booked', 'pending_approval')
            """
        )
        op.execute(
            """
            UPDATE doctor_schedule_exceptions
            SET kind = 'blocked_interval'
            WHERE kind = 'custom'
            """
        )
        op.execute(
            """
            UPDATE registration_requests rr
            SET status = 'declined', updated_at = CURRENT_TIMESTAMP
            WHERE rr.status IN ('pending', 'approved')
              AND EXISTS (
                  SELECT 1
                  FROM auth_users au
                  JOIN patients p ON p.id = au.patient_id
                  WHERE au.id = rr.patient_id
                    AND p.doctor_id IS NOT NULL
                    AND p.doctor_id <> rr.doctor_id
              )
            """
        )
        return

    bind = op.get_bind()
    appointments = bind.execute(
        sa.text(
            """
            SELECT id, appointment_date, start_time, end_time, timezone, status
            FROM appointments
            """
        )
    ).mappings()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for row in appointments:
        schedule_timezone = row["timezone"] or "UTC"
        start_at = _utc_naive(
            row["appointment_date"], row["start_time"], schedule_timezone
        )
        end_at = _utc_naive(
            row["appointment_date"], row["end_time"], schedule_timezone
        )
        status = row["status"]
        cancellation_reason = None
        if end_at and end_at <= now and status == "booked":
            status = "awaiting_outcome"
        elif end_at and end_at <= now and status == "pending_approval":
            status = "cancelled"
            cancellation_reason = "registration_request_expired"
        bind.execute(
            sa.text(
                """
                UPDATE appointments
                SET schedule_timezone = :schedule_timezone,
                    start_at_utc = :start_at,
                    end_at_utc = :end_at,
                    status = :status,
                    cancellation_reason = COALESCE(
                        cancellation_reason, :cancellation_reason
                    )
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "schedule_timezone": schedule_timezone,
                "start_at": start_at,
                "end_at": end_at,
                "status": status,
                "cancellation_reason": cancellation_reason,
            },
        )

    # Legacy "custom" rows represented blocked intervals. Preserve their behavior
    # under the explicit blocked_interval type before custom becomes replacement hours.
    bind.execute(
        sa.text(
            """
            UPDATE doctor_schedule_exceptions
            SET kind = 'blocked_interval'
            WHERE kind = 'custom'
            """
        )
    )

    # Patient assignment is authoritative. Close stale approved/pending requests
    # that point at a different doctor instead of silently rewriting assignments.
    bind.execute(
        sa.text(
            """
            UPDATE registration_requests rr
            SET status = 'declined', updated_at = :now
            WHERE rr.status IN ('pending', 'approved')
              AND EXISTS (
                  SELECT 1
                  FROM auth_users au
                  JOIN patients p ON p.id = au.patient_id
                  WHERE au.id = rr.patient_id
                    AND p.doctor_id IS NOT NULL
                    AND p.doctor_id <> rr.doctor_id
              )
            """
        ),
        {"now": now},
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE doctor_schedule_exceptions
            SET kind = 'custom'
            WHERE kind = 'blocked_interval'
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE appointments
            SET status = 'booked'
            WHERE status = 'awaiting_outcome'
            """
        )
    )
    op.drop_index("ix_appointments_end_at_utc", table_name="appointments")
    op.drop_index("ix_appointments_start_at_utc", table_name="appointments")
    op.drop_constraint(
        "fk_appointments_outcome_recorded_by",
        "appointments",
        type_="foreignkey",
    )
    op.drop_column("appointments", "outcome_recorded_by")
    op.drop_column("appointments", "outcome_recorded_at")
    op.drop_column("appointments", "cancellation_reason")
    op.drop_column("appointments", "end_at_utc")
    op.drop_column("appointments", "start_at_utc")
    op.drop_column("appointments", "schedule_timezone")
    op.drop_column("auth_users", "token_version")
