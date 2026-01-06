import base64
from datetime import datetime, timedelta
from io import BytesIO
import uuid
from django.http import HttpResponse
from django.shortcuts import render
import jinja2
import qrcode
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
import json
from adrf.viewsets import GenericViewSet as AsyncGenericViewSet
from asgiref.sync import sync_to_async
from django.db.models import Q
from sqlalchemy import Transaction
from weasyprint import HTML
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ivg.serializers import InvoiceDataSerializer
from django.db import transaction
# Create your views here.
templates = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=True
)


class HealthCheckViewSet(APIView):
    def get(self, request):
        return Response({
            "success": True,
            "data": "Server Healthy", 
            "error": None
        })
    
class InvoiceCreationViewSet(AsyncGenericViewSet) :
    permission_classes = [IsAuthenticated , IsAdminUser]
    serializer_class = InvoiceDataSerializer

    async def generate_qr_data(self , token: str , data) -> str:
        now = datetime.utcnow()
        expiry = now + timedelta(hours=2)
        qr_data = {
            "day": now.strftime("%A"),  # Monday
            "date": now.strftime("%Y-%m-%d"),  # 2026-01-04
            "time": now.strftime("%H:%M"),  # 17:06
            "expired_time": expiry.strftime("%Y-%m-%d %H:%M"),  # 2026-01-04 19:06
            "sl_no": data["id"],
            "car_number": data["car_number"],
            "wheels": data["wheels"],
            "location": data["location"],
            "cft": data["cft"],
            "expiry_ts": int(expiry.timestamp() * 1000)  # JS timestamp
        }
        return json.dumps(qr_data) 
    
    @sync_to_async
    def validate_and_save(self , data , user) :
        try :
            serializer = InvoiceDataSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=user)
            return serializer.data     
        except Exception as e :
            raise ValueError(str(e))

    
    @action(detail=False , methods=['post'] , url_path='generate')
    async def generate_invoice(self , request) :
        try :
            data = await self.validate_and_save(request.data , request.user)

                # Generate unique token for QR (2-hour expiry)
            token = str(uuid.uuid4())
            qr_data = await self.generate_qr_data(token , data)
                
            # Generate QR as base64
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
                
            print(data)
                # Render template - pass raw data only

            created_at_str = data["created_at"]
            created_at_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            formatted_date = created_at_dt.strftime("%d-%m-%Y %H:%M")
            template = templates.get_template("invoice.html")
            
            html_content = template.render(
                    sl_no=data["id"],
                    car_number=data["car_number"],
                    date_time=formatted_date,
                    wheels=data["wheels"],
                    cargo_type=data["location"],
                    cft=data["cft"],
                    qr_base64=qr_base64,
                    token=token[:8]
            )
        
                # Generate PDF
            html = HTML(string=html_content)
            pdf_bytes = html.write_pdf()
                
            filename = f"invoice-{data["car_number"].replace(' ', '')}-{token[:8]}.pdf"
            response = HttpResponse(
                    pdf_bytes,
                    content_type="application/pdf"
                )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            return response
        except Exception as e :
            return Response(
            {"error": str(e)},
            status=400
        )