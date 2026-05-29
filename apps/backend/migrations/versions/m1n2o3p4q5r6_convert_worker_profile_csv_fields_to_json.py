"""Convert worker_profile CSV fields to JSON arrays.

Revision ID: m1n2o3p4q5r6
Revises: l1m2n3o4p5q6
Create Date: 2026-05-23

skills, available_days, and available_shifts were stored as comma-separated
strings (e.g. "Security,Guard"). They are now stored as JSON arrays
(e.g. ["Security", "Guard"]) so callers receive typed arrays via the API
and queries no longer need CSV parsing.
"""
import json as _json

import sqlalchemy as sa
from alembic import op

revision = "m1n2o3p4q5r6"
down_revision = "l1m2n3o4p5q6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("worker_profiles") as batch_op:
        batch_op.add_column(sa.Column("skills_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("available_days_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("available_shifts_json", sa.JSON(), nullable=True))

    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        # string_to_array splits on comma and to_json converts the text[] to a JSON array.
        bind.execute(sa.text("""
            UPDATE worker_profiles SET
                skills_json           = CASE WHEN skills IS NULL THEN NULL
                                             ELSE to_json(string_to_array(trim(skills), ',')) END,
                available_days_json   = CASE WHEN available_days IS NULL THEN NULL
                                             ELSE to_json(string_to_array(trim(available_days), ',')) END,
                available_shifts_json = CASE WHEN available_shifts IS NULL THEN NULL
                                             ELSE to_json(string_to_array(trim(available_shifts), ',')) END
        """))
    else:
        # SQLite: iterate rows and convert in Python.
        rows = bind.execute(
            sa.text("SELECT id, skills, available_days, available_shifts FROM worker_profiles")
        ).mappings().fetchall()

        def _to_list(csv_val):
            if not csv_val:
                return None
            return [s.strip() for s in csv_val.split(",") if s.strip()]

        for row in rows:
            bind.execute(
                sa.text(
                    "UPDATE worker_profiles SET "
                    "skills_json = :s, available_days_json = :d, available_shifts_json = :sh "
                    "WHERE id = :id"
                ),
                {
                    "s": _json.dumps(_to_list(row["skills"])) if row["skills"] else None,
                    "d": _json.dumps(_to_list(row["available_days"])) if row["available_days"] else None,
                    "sh": _json.dumps(_to_list(row["available_shifts"])) if row["available_shifts"] else None,
                    "id": row["id"],
                },
            )

    with op.batch_alter_table("worker_profiles") as batch_op:
        batch_op.drop_column("skills")
        batch_op.drop_column("available_days")
        batch_op.drop_column("available_shifts")
        batch_op.alter_column("skills_json", new_column_name="skills")
        batch_op.alter_column("available_days_json", new_column_name="available_days")
        batch_op.alter_column("available_shifts_json", new_column_name="available_shifts")


def downgrade() -> None:
    with op.batch_alter_table("worker_profiles") as batch_op:
        batch_op.add_column(sa.Column("skills_csv", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("available_days_csv", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("available_shifts_csv", sa.String(100), nullable=True))

    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        bind.execute(sa.text("""
            UPDATE worker_profiles SET
                skills_csv           = CASE WHEN skills IS NULL THEN NULL
                                             ELSE array_to_string(
                                                 ARRAY(SELECT jsonb_array_elements_text(skills::jsonb)), ','
                                             ) END,
                available_days_csv   = CASE WHEN available_days IS NULL THEN NULL
                                             ELSE array_to_string(
                                                 ARRAY(SELECT jsonb_array_elements_text(available_days::jsonb)), ','
                                             ) END,
                available_shifts_csv = CASE WHEN available_shifts IS NULL THEN NULL
                                             ELSE array_to_string(
                                                 ARRAY(SELECT jsonb_array_elements_text(available_shifts::jsonb)), ','
                                             ) END
        """))
    else:
        rows = bind.execute(
            sa.text("SELECT id, skills, available_days, available_shifts FROM worker_profiles")
        ).mappings().fetchall()

        def _to_csv(json_val):
            if not json_val:
                return None
            items = _json.loads(json_val) if isinstance(json_val, str) else json_val
            return ",".join(items) if items else None

        for row in rows:
            bind.execute(
                sa.text(
                    "UPDATE worker_profiles SET "
                    "skills_csv = :s, available_days_csv = :d, available_shifts_csv = :sh "
                    "WHERE id = :id"
                ),
                {
                    "s": _to_csv(row["skills"]),
                    "d": _to_csv(row["available_days"]),
                    "sh": _to_csv(row["available_shifts"]),
                    "id": row["id"],
                },
            )

    with op.batch_alter_table("worker_profiles") as batch_op:
        batch_op.drop_column("skills")
        batch_op.drop_column("available_days")
        batch_op.drop_column("available_shifts")
        batch_op.alter_column("skills_csv", new_column_name="skills")
        batch_op.alter_column("available_days_csv", new_column_name="available_days")
        batch_op.alter_column("available_shifts_csv", new_column_name="available_shifts")
