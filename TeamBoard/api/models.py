from django.conf import settings
from django.db import models

# Create your models here.
class Company(models.Model):
    class Role(models.TextChoices):
        CLIENT = 'client', 'Client'
        ADMIN = 'admin', 'Admin'
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company'
    )
    company_name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT
    )
    created_at = models.DateTimeField(auto_now_add=True)

# KB Entry model
class KBEntry(models.Model):
    class Category(models.TextChoices):
        API = 'api', 'API'
        DATABASE = 'database', 'Database'
        CLOUD = 'cloud', 'Cloud'
        FRAMEWORKS = 'frameworks', 'Frameworks'
        GENERAL = 'general', 'General'
    
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question[:80]  # Return the first 80 characters of the question for easy identification

# Query Log model
class QueryLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='query_logs')
    # query = models.TextField()
    # response = models.TextField()
    search_team = models.CharField(max_length=255)
    result_count = models.IntegerField()
    queried_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QueryLog {self.id} for {self.company.company_name} at {self.queried_at}"