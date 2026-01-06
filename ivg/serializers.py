from django.contrib.auth import get_user_model
from rest_framework import serializers

from ivg.models import InvoiceData


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