import base64
from datetime import datetime, timedelta
from io import BytesIO
import uuid
from django.db.models import Sum, Count, Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import render
import jinja2
import qrcode
from rest_framework.permissions import  IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from adrf.viewsets import GenericViewSet as AsyncGenericViewSet
from asgiref.sync import sync_to_async
from django.db.models import Q
from weasyprint import HTML
from ivg.constant import PayMentStatus, PaymentMethodType
from ivg.models import InvoiceData
from ivg.serializers import InvoiceDataListSerializer, InvoiceDataSerializer

# Create your views here.
templates = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=True
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20  # Default 20 items per page
    page_size_query_param = 'page_size'
    max_page_size = 100


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
    pagination_class = StandardResultsSetPagination

    async def generate_qr_data(self , data , creation_time) -> str:

        qr_text = f"""
                E-Challan (Sand Stock)
                Challan No        : {data['id']}
                Generated Date    : {creation_time}
                Vehicle No        : {data['car_number']}
                WHEELS            : {data['wheels']}
                Location          : {data['location']}
                Quantity (CFT)    : {data['cft']}
                """.strip()

        return qr_text
    
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

            created_at_str = data["created_at"]
            created_at_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            formatted_date = created_at_dt.strftime("%d-%m-%Y %H:%M")

            qr_data = await self.generate_qr_data(data , formatted_date)
                
            # Generate QR as base64
            qr = qrcode.QRCode(version=None, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
                
            print("DEBUG CHALAN DATA : - " , data)
                # Render template - pass raw data only

            
            template = templates.get_template("invoice.html")

            html_content = template.render(
                    sl_no=data["id"],
                    car_number=data["car_number"],
                    date_time=formatted_date,
                    wheels=data["wheels"],
                    cargo_type=data["location"],
                    cft=data["cft"],
                    qr_base64=qr_base64
            )
        
                # Generate PDF
            html = HTML(string=html_content)
            pdf_bytes = html.write_pdf()
                
            filename = f"invoice-{data["car_number"].replace(' ', '')}-{data['id']}.pdf"
            pdf_buffer = BytesIO(pdf_bytes)
            return FileResponse(
                pdf_buffer,
                as_attachment=False,
                filename=filename,
                content_type="application/pdf"
            )
        except Exception as e :
            return Response(
            {"error": str(e)},
            status=400
        )

    @action(detail=False , methods=['get'] , url_path='list')
    def list_invoices(self , request) :
        try :

            invoices = InvoiceData.objects.all().order_by('-created_at')
            print("DEBUG INVOICE QS :- " , invoices)

            paginator =  self.pagination_class()
            page = paginator.paginate_queryset(invoices, request)
            
            print("DEBUG INVOICE PAGE :- " , page)
            serializer = InvoiceDataListSerializer(page, many=True)

            
            return Response(serializer.data)

            
        except Exception as e :
            return Response(
            {
                    "success" : False ,
                    "data" :  None,
                    "error" : str(e)
                },
            status=400
        )
    
    @action(detail=False, methods=['get'], url_path='stats')
    async def stats(self, request):
        try :
            user = request.user
            stats = await sync_to_async(lambda : InvoiceData.objects.filter(created_by=user).aggregate(
            total_entries=Count("id"),
            total_amount=Sum("paid_amount"),
            total_cash_amount=Sum(
                "paid_amount",
                filter=Q(payment_in=PaymentMethodType.CASH.value)
            ),
            total_upi_amount=Sum(
                "paid_amount",
                filter=Q(payment_in=PaymentMethodType.UPI.value)
            ),
        ))()

            response_data = {
                "total_entries": stats["total_entries"] or 0,
                "total_amount": stats["total_amount"] or 0,
                "total_paid_cash": stats["total_cash_amount"] or 0,
                "total_paid_upi": stats["total_upi_amount"] or 0,
            }

            return Response(
                {
                    "success": True,
                    "data": response_data,
                    "error": None
                }
            )
        
        except Exception as e :
            return Response(
            {"error": str(e)},
            status=400
        )