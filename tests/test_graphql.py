"""
Тесты GraphQL API.
Проверяют защищённые поля, мутации и директивы.
"""


def test_graphql_me_without_token(client):
    """Запрос me без токена должен вернуть ошибку аутентификации."""
    res = client.post("/graphql", json={
        "query": "{ me { email } }"
    })
    assert res.status_code == 200
    data = res.json()
    assert "errors" in data
    assert "Authentication required" in data["errors"][0]["message"]


def test_graphql_users_without_admin(client):
    """Запрос users без админ-прав должен вернуть ошибку."""
    # Регистрируем обычного пользователя
    res = client.post("/auth/register", json={
        "email": "user@vault.com",
        "password": "MySuperSecretPassword2024!"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token is not None

    # Пробуем запросить список пользователей
    res = client.post("/graphql", json={
        "query": "{ users { email } }"
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    data = res.json()
    assert "errors" in data
    assert "Admin only" in data["errors"][0]["message"]


def test_graphql_clients_without_admin(client):
    """Запрос clients без админ-прав должен вернуть ошибку."""
    res = client.post("/auth/register", json={
        "email": "user2@vault.com",
        "password": "MySuperSecretPassword2024!"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token is not None

    res = client.post("/graphql", json={
        "query": "{ clients { clientId name } }"
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    data = res.json()
    assert "errors" in data
    assert "Admin only" in data["errors"][0]["message"]


def test_graphql_register_and_me(client):
    """Регистрация через GraphQL и получение me."""
    # Регистрация через GraphQL
    res = client.post("/graphql", json={
        "query": """
        mutation {
            registerUser(email: "gql@vault.com", password: "MySuperSecretPassword2024!") {
                accessToken
                tokenType
            }
        }
        """
    })
    assert res.status_code == 200
    data = res.json()
    assert "errors" not in data
    token = data["data"]["registerUser"]["accessToken"]
    assert token is not None

    # Запрос me с полученным токеном
    res = client.post("/graphql", json={
        "query": "{ me { email isAdmin } }"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["data"]["me"]["email"] == "gql@vault.com"
    assert data["data"]["me"]["isAdmin"] is False


def test_graphql_register_duplicate_email(client):
    """Повторная регистрация с тем же email должна вернуть ошибку."""
    query = """
    mutation {
        registerUser(email: "dup@vault.com", password: "MySuperSecretPassword2024!") {
            accessToken
        }
    }
    """
    res = client.post("/graphql", json={"query": query})
    assert res.status_code == 200
    assert "errors" not in res.json()

    # Повторная регистрация
    res = client.post("/graphql", json={"query": query})
    assert res.status_code == 200
    data = res.json()
    assert "errors" in data
    assert "already registered" in data["errors"][0]["message"].lower()