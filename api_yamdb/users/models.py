from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    class UserRole(models.TextChoices):
        USER = 'user'
        MODERATOR = 'moderator'
        ADMIN = 'admin'

    username = models.CharField(
        max_length=150,
        verbose_name='Логин',
        help_text='Укажите логин',
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='Имя пользователя содержит недопустимый символ'
        )]
    )
    email = models.EmailField(
        max_length=254,
        verbose_name='Email',
        help_text='Укажите email',
        unique=True
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        help_text='Укажите Ваше имя',
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        help_text='Укажите Вашу фамилию',
        blank=True,
        null=True,
    )
    bio = models.TextField(
        max_length=1000,
        verbose_name='Биография',
        help_text='Расскажите о себе',
        blank=True,
        null=True,
    )
    role = models.CharField(
        max_length=20,
        verbose_name='Роль',
        choices=UserRole.choices,
        default=UserRole.USER,
        help_text='Роль пользователя'
    )
    confirmation_code = models.CharField(
        max_length=6,
        blank=True,
        verbose_name='Проверочный код')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.UserRole.ADMIN

    @property
    def is_moderator(self):
        return self.role == self.UserRole.MODERATOR

    @property
    def is_user(self):
        return self.role == self.UserRole.USER
