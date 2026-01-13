import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

from ivg.constant import PayMentStatus, PaymentMethodType, TripStatusType

class Base(models.Model):
    """Base model that provides UUID primary key for all models"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Vendors(Base) :
    name = models.CharField(max_length=255, unique=True)
    additional_info = models.JSONField(null=True , blank=True)
    slug = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"BRANCH - {self.name}"
    

class Branches(Base):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(null=True , blank= True)
    additional_info = models.JSONField(null=True , blank=True)
    slug = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"BRANCH - {self.name}"

class InvoiceUser(AbstractUser):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, primary_key=True, unique=True
    )
    is_ultraadmin = models.BooleanField(
        default=False, help_text="Designates whether the user is a Ultraadmin user."
    )
    is_superadmin = models.BooleanField(
        default=False , help_text="Represent The Super Admin User"
    )
    is_coofficer = models.BooleanField(
        default=False , help_text="Represent The Co-Officer"
    )
    is_admin = models.BooleanField(
        default=True , help_text="Represent The Normal User"
    )
    branch = models.ForeignKey(Branches , on_delete=models.CASCADE , null=True , blank=True)

    @property
    def user_type(self):
        if self.is_ultraadmin:
            return "ultraadmin"
        elif self.is_superadmin:
            return "superadmin"
        elif self.is_coofficer:
            return "coofficer"
        elif self.is_admin:
            return "adminuser"
        else:
            return "user"
        
    def __str__(self):
        return f"{self.username} - {self.user_type}"




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
    remarks = models.TextField(null=True , blank=True)

    class Meta :
        ordering = ['-created_at' , '-updated_at']

    def __str__(self):
        return f"{str(self.name)} PICKED -- WEIGHT :- {self.cft}" 
    