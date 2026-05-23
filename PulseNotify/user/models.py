from django.db import models

# import user from django
from django.contrib.auth.models import User

class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    created_at = models.DateTimeField(auto_now_add=True)

class priceAlert(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        TRIGGERED = 'triggered', 'Triggered'
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts')
    orign = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    # departure_date = models.DateField()
    treshold_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.orign} to {self.destination} at ₹{self.treshold_price} ({self.status})"

class notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    trigered_price_alert = models.ForeignKey(priceAlert, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notified_at = models.DateTimeField(auto_now_add=True)