import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database.models import Base
from main import app
from src.api.tools import get_db

# Создаем тестовую базу данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы в тестовой базе
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_rate_limiter():
    # Тестируем ограничение запросов
    for _ in range(60):
        response = client.get("/health")
        assert response.status_code == 200
    
    response = client.get("/health")
    assert response.status_code == 429

def test_error_handler():
    response = client.get("/non_existent_endpoint")
    assert response.status_code == 404
    assert "detail" in response.json()

def test_chat_logs_pagination():
    response = client.get("/api/v1/logs?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
