import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.main import app
from app.db.session import Base, get_db, SessionLocal

# 1. Настройка тестовой БД
TEST_DB_URL = "sqlite:///./test_vault.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Переопределение зависимости для REST-роутов FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 3. Фикстура для очистки БД перед каждым тестом
@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# 4. Фикстура клиента с патчингом SessionLocal для GraphQL
@pytest.fixture
def client():
    # Патчим SessionLocal везде, где он может быть импортирован
    with patch("app.db.session.SessionLocal", TestingSessionLocal):
        with patch("app.graphql.context.SessionLocal", TestingSessionLocal):
            with TestClient(app) as c:
                yield c