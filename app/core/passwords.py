from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from zxcvbn import zxcvbn
from app.config import settings



ph = PasswordHasher(
    time_cost=3,       # Количество итераций
    memory_cost=65536, # 64 МБ памяти
    parallelism=4,     # Потоки
    hash_len=32,       # Длина хэша
    salt_len=16        # Длина соли
)


class WeakPasswordError(Exception):
   
    pass


def hash_password(password: str) -> str:
   
    return ph.hash(password + settings.password_pepper)


def verify_password(password: str, hashed: str) -> bool:

    try:
        return ph.verify(hashed, password + settings.password_pepper)
    except VerifyMismatchError:
        return False


def validate_policy(password: str, user_inputs: list[str] = None):
   
  
    if len(password) < settings.password_min_length:
        raise WeakPasswordError(
            f"Пароль должен содержать минимум {settings.password_min_length} символов."
        )

    result = zxcvbn(password, user_inputs=user_inputs)
    

    if result["score"] < 3:
        raise WeakPasswordError(
            "Пароль слишком простой. "
            "Используйте более сложную комбинацию букв, цифр и символов."
        )