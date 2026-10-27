import pytest
from app.core.passwords import hash_password, verify_password, validate_policy, WeakPasswordError


def test_strong_password():
    """Сложный пароль должен проходить проверку без исключений."""
    validate_policy("MySuperSecretPassword2024!", user_inputs=["test@vault.com"])


def test_weak_password_length():
    """Слишком короткий пароль должен отклоняться."""
    with pytest.raises(WeakPasswordError):
        validate_policy("Short1!", user_inputs=["test@vault.com"])


def test_weak_password_zxcvbn():
    """Длинный, но очень предсказуемый пароль должен отклоняться."""
    with pytest.raises(WeakPasswordError):
        validate_policy("password12345678", user_inputs=["test@vault.com"])


def test_password_contains_email():
    """Пароль, совпадающий с email, должен отклоняться."""
    # Используем пароль, который точно совпадает с email
    with pytest.raises(WeakPasswordError):
        validate_policy("test@vault.com", user_inputs=["test@vault.com"])


def test_hash_and_verify():
    """Хэширование и проверка пароля должны работать корректно."""
    pwd = "MySuperSecretPassword2024!"
    hashed = hash_password(pwd)
    
    # Правильный пароль должен проходить проверку
    assert verify_password(pwd, hashed) is True
    
    # Неправильный пароль должен отклоняться
    assert verify_password("wrong_password", hashed) is False