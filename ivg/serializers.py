from django.contrib.auth import get_user_model
from rest_framework import serializers

from ivg.models import InvoiceData, InvoiceUser


class InvoiceDataSerializer(serializers.ModelSerializer) :

    class Meta :
        model = InvoiceData
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "created_by",
        )

class InvoiceUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceUser
        fields = ['id', 'username', 'email' , 'first_name' ,'last_name', 'is_superuser']  # Add more fields as needed: email, first_name, etc.

class InvoiceDataListSerializer(serializers.ModelSerializer):
    created_by = InvoiceUserSerializer(read_only=True)  # Nested user details
    
    class Meta:
        model = InvoiceData
        fields = [
            'id', 'created_by', 'trip', 'police_station', 'car_number', 
            'phone_number', 'name', 'location', 'wheels', 'cft', 
            'total_cost', 'payment_in', 'paid_amount', 'payment_status', 
            'remarks', 'created_at' , 'updated_at'
        ]