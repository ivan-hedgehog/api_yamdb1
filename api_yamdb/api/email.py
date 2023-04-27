from django.conf import settings
from django.core.mail import send_mail


def send_confirmation_code(email, confirmation_code):
    """Oтправляет на почту пользователя код подтверждения."""
    send_mail(
        subject='Код подтверждения',
        message=f'Ваш код подтверждения: {confirmation_code}',
        from_email=settings.ADMIN_EMAIL,
        recipient_list=(email,),
        fail_silently=False,
    )
