from sqlalchemy import inspect, text

from app.extensions import db


def test_committed_initial_migration_upgrades_database(app):
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = set(inspector.get_table_names())

        assert {"users", "training_sessions", "questions", "answers"} <= table_names
        revision = db.session.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        assert revision
