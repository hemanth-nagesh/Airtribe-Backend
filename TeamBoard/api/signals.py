import secrets
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Company

User = get_user_model()


@receiver(post_save, sender=User)
def create_company(sender, instance, created, **kwargs):
    if created:
        Company.objects.create(
            user=instance,
            company_name = instance.email,
            api_key=secrets.token_urlsafe(32)
            )