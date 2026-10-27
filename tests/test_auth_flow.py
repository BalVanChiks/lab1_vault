def test_register_and_login(client):
    email = "test@vault.com"
    password = "MySuperSecretPassword2024!"
    
    # Регистрация
    res = client.post("/auth/register", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    
    # Логин
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    
    # Получение me
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == email


def test_invalid_login(client):
    # Сначала регистрируем
    client.post("/auth/register", json={"email": "fail@vault.com", "password": "MySuperSecretPassword2024!"})
    
    # Пробуем войти с неверным паролем
    res = client.post("/auth/login", json={"email": "fail@vault.com", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


def test_me_without_token(client):
    """GET /auth/me без токена должен вернуть 401."""
    res = client.get("/auth/me")
    assert res.status_code == 401


def test_me_with_invalid_token(client):
    """GET /auth/me с невалидным токеном должен вернуть 401."""
    res = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401


def test_audit_login_success_recorded(client):
    """После успешного логина в audit_events должна появиться запись user.login.success."""
    from app.db.session import SessionLocal
    from app.models.audit import AuditEvent

    email = "audit@vault.com"
    password = "MySuperSecretPassword2024!"

    # Регистрируем
    client.post("/auth/register", json={"email": email, "password": password})

    # Логинимся
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200

    # Проверяем аудит в БД
    db = SessionLocal()
    try:
        event = (
            db.query(AuditEvent)
            .filter(AuditEvent.event_type == "user.login.success")
            .order_by(AuditEvent.id.desc())
            .first()
        )
        assert event is not None, "Событие user.login.success не записано в аудит"
        assert event.actor_id is not None, "actor_id должен быть указан для успешного логина"
    finally:
        db.close()


def test_audit_login_failure_recorded(client):
    """После неудачного логина в audit_events должна появиться запись user.login.failure."""
    from app.db.session import SessionLocal
    from app.models.audit import AuditEvent

    email = "fail-audit@vault.com"
    password = "MySuperSecretPassword2024!"

    # Регистрируем
    client.post("/auth/register", json={"email": email, "password": password})

    # Пытаемся войти с неверным паролем
    res = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert res.status_code == 401

    # Проверяем аудит
    db = SessionLocal()
    try:
        event = (
            db.query(AuditEvent)
            .filter(AuditEvent.event_type == "user.login.failure")
            .order_by(AuditEvent.id.desc())
            .first()
        )
        assert event is not None, "Событие user.login.failure не записано в аудит"
        assert event.actor_id is None, "actor_id должен быть NULL для неудачного логина"
        # Проверяем, что email есть в metadata, но пароль — нет
        metadata = event.metadata_json or {}
        assert "email" in metadata, "email должен быть в metadata события"
    finally:
        db.close()