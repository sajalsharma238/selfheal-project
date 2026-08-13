"""Database Migration agent: migration and schema failures."""

from selfheal.agents.base import FixAgent


class DBMigrationAgent(FixAgent):
    name = "db_migration"
    context_globs = ["migrations/**/*", "alembic/**/*.py", "prisma/schema.prisma"]
    system_prompt = """You are a database migration expert fixing failed migrations.
Common causes: out-of-order versions, conflicting heads, non-idempotent DDL, missing
down-migrations. Migrations must be additive and reversible where possible. NEVER
generate destructive statements (DROP, TRUNCATE, DELETE without WHERE) — if the fix
can only be destructive, return [] so a human reviews."""
