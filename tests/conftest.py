import pytest
from app import database as db


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', str(tmp_path / 'test.db'))
    monkeypatch.setattr(db, 'DATABASE_URL', f'sqlite:///{tmp_path / "test.db"}')
    monkeypatch.setattr(db, '_engine', None)
    monkeypatch.setattr(db, '_SessionLocal', None)
    db.init_db()
    yield db
    db.get_engine().dispose()
