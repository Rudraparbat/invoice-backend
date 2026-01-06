import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

from ivg.constant import PayMentStatus, PaymentMethodType, TripStatusType


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


class Base(models.Model):
    """Base model that provides UUID primary key for all models"""

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class InvoiceData(Base) :
    created_by = models.ForeignKey(InvoiceUser, on_delete=models.CASCADE)  
    trip = models.CharField(max_length=50, choices=TripStatusType.choices())
    police_station = models.CharField(max_length=160 , null=True , blank=True)
    car_number = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=13)
    name = models.CharField(max_length=299)
    location = models.CharField(max_length=300)
    wheels = models.IntegerField()
    cft = models.FloatField()
    total_cost = models.FloatField()
    payment_in = models.CharField(max_length=50, choices=PaymentMethodType.choices())
    paid_amount = models.FloatField()
    payment_status = models.CharField(max_length=50, choices=PayMentStatus.choices())
    remarks = models.TextField(null=True , blank=True)

    class Meta :
        ordering = ['-created_at' , '-updated_at']

    def __str__(self):
        return f"{str(self.name)} PICKED -- WEIGHT :- {self.cft}" 
    