import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class InvoiceUser(AbstractUser):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    is_system = models.BooleanField(
        default=False, help_text="Designates whether the user is a system user."
    )
    

    @property
    def user_type(self):
        if self.is_superuser:
            return "admin"
        elif self.is_system:
            return "system"
        else:
            return "user"

    def save(self, *args, **kwargs):
        # If user is admin, set agent_manager and is_system to True
        if self.is_superuser:
            self.is_system = True
        super().save(*args, **kwargs)