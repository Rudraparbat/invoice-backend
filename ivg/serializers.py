from django.contrib.auth import get_user_model
from rest_framework import serializers

from ivg.models import Branches, InvoiceData, InvoiceUser


class InvoiceGenerationSerializer(serializers.ModelSerializer):
    # Separate formatted fields
    created_by_name = serializers.SerializerMethodField()  # Bonus: user display
    
    class Meta:
        model = InvoiceData
        fields = [
            'id', 'trip', 'police_station', 'car_number', 
            'phone_number', 'name', 'location', 'wheels', 
            'cft', 'remarks',
            'created_by_name'
        ]
        read_only_fields = ('id', 'created_by_name')
    
    def get_created_by_name(self, obj):
        return f"{obj.created_by.username}".strip()


class BranchSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Branches
        fields = '__all__'
    
class InvoiceUserSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(many=True)
    class Meta:
        model = InvoiceUser
        fields = ['id', 'branch' , 'username', 'email' , 'first_name' ,'last_name', 'user_type']  # Add more fields as needed: email, first_name, etc.

class InvoiceUserCreateSerializer(serializers.ModelSerializer) :
    class Meta :
        model = InvoiceUser
    
class UltraAdminDashBoardSerializer(serializers.Serializer) :
    total_branches = serializers.IntegerField()
    total_users = serializers.IntegerField()
    
class InvoiceDataListSerializer(serializers.ModelSerializer):
    created_by = InvoiceUserSerializer(read_only=True)  # Nested user details
    
    class Meta:
        model = InvoiceData
        fields = [
            'id', 'created_by', 'trip', 'police_station', 'car_number', 
            'phone_number', 'name', 'location', 'wheels', 'cft', 
            'remarks', 'created_at' , 'updated_at'
        ]


