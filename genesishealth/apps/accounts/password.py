import random
import re
import string
from typing import Optional

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User


def make_password(user: Optional[User] = None) -> str:
    while True:
        special_chars = "!@#$%^&*()"
        length = random.randint(8, 12)
        num_count = random.randint(1, 3)
        upper_count = random.randint(1, length - 2 - num_count)
        lower_count = length - upper_count - 1 - num_count
        spec_char = random.choice(special_chars)
        upper_letters = [
            random.choice(string.ascii_uppercase)
            for _ in range(upper_count)
        ]
        lower_letters = [
            random.choice(string.ascii_lowercase)
            for _ in range(lower_count)
        ]
        nums = [
            str(random.choice(range(10)))
            for _ in range(num_count)
        ]
        password_l = upper_letters + lower_letters + [spec_char] + nums
        random.shuffle(password_l)
        password = "".join(password_l)
        if user is None:
            return password
        try:
            validate_password(user, password)
        except AssertionError:
            continue
        else:
            return password


def set_password(user: User, new_password: str) -> None:
    from genesishealth.apps.accounts.models.profile_base import (
        PreviousPassword)
    validate_password(user, new_password)
    user.set_password(new_password)
    user.save()
    PreviousPassword.objects.create(user=user, password=user.password)


def validate_password(user: User, new_password: str) -> None:
    assert bool(re.findall(r"[%$#@!^&*()]", new_password)),\
        "You must include at least one special character: !@#$%^&*()"
    assert bool(re.findall(r"\d", new_password)),\
        "You must include at least one number in your password."
    assert bool(re.findall(r"[A-Z]", new_password)),\
        "You must include at least one capital letter in your password."
    assert bool(re.findall(r"[a-z]", new_password)),\
        "You must include at least one lowercase letter in your password."
    assert len(new_password) >= 8,\
        "Your password must be at least eight letters long."
    previous_passwords = map(
        lambda x: not check_password(new_password, x['password']),
        user.previous_passwords.values('password')[:4]
    )
    assert all(previous_passwords), "You must use a password different from your last four."
