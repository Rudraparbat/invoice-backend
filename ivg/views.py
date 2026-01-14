from rest_framework.permissions import  IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView , status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet , mixins
from ivg.models import Branches, InvoiceData, InvoiceUser
from ivg.serializers import BranchSerializer, InvoiceDataListSerializer, InvoiceGenerationSerializer, InvoiceUserSerializer, UltraAdminDashBoardSerializer, FileUploadSerializer, PresignedURLSerializer, UpdateInvoiceFileSerializer
from ivg.permissions import UltraAdminPermission 
import requests
import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings 


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
    
class BranchViewSet(GenericViewSet ,
                    mixins.CreateModelMixin , 
                    mixins.ListModelMixin ,
                    mixins.DestroyModelMixin ,
                    mixins.RetrieveModelMixin ,
                    mixins.UpdateModelMixin) :
    """
    Only Authenticated UltraAdmin Can Access The ViewSet
    """
    permission_classes = [IsAuthenticated , UltraAdminPermission]
    pagination_class = StandardResultsSetPagination
    serializer_class = BranchSerializer
    queryset = Branches.objects.all()


class UserManagementViewSet(GenericViewSet ,
                            mixins.CreateModelMixin , 
                            mixins.ListModelMixin ,
                            mixins.DestroyModelMixin ,
                            mixins.UpdateModelMixin ,
                            mixins.RetrieveModelMixin) :

    """
    user Management Only For UltraAdmin
    """

    permission_classes = [IsAuthenticated , UltraAdminPermission]
    pagination_class = StandardResultsSetPagination
    serializer_class = InvoiceUserSerializer
    queryset = InvoiceUser.objects.filter(is_ultraadmin=False)

class UltraAdminDashBoardViewSet(GenericViewSet) :
    permission_classes = [IsAuthenticated , UltraAdminPermission]
    serializer_class = UltraAdminDashBoardSerializer
    
    @action(detail=False , methods=['get'] , url_path='ultradmin/stats')
    def ultraadmin_stat(self , request) :
        try :
            # retreive branch users together 
            pass
        except Exception as e :
            return Response({"detail" : str(e)} , status=status.HTTP_400_BAD_REQUEST)

class InvoiceCreationViewSet(GenericViewSet , mixins.CreateModelMixin , mixins.ListModelMixin) :

    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceGenerationSerializer
    pagination_class = StandardResultsSetPagination
    

    def get_serializer_class(self):
        if self.action in ['create' , 'update'] :
            return InvoiceGenerationSerializer
        return InvoiceDataListSerializer
    
    def get_queryset(self):
        return InvoiceData.objects.filter(
                created_by__branch=self.request.user.branch 
        )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=201)


class FileUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FileUploadSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data['url']
        invoice_id = serializer.validated_data['invoice_id']

        try:
            invoice = InvoiceData.objects.get(id=invoice_id, created_by__branch=request.user.branch)
        except InvoiceData.DoesNotExist:
            return Response({"error": "Invoice not found or not accessible"}, status=status.HTTP_404_NOT_FOUND)

        # Download the file
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            file_content = response.content
        except requests.RequestException as e:
            return Response({"error": f"Failed to download file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check file size < 5MB
        max_size = 5 * 1024 * 1024  # 5MB
        if len(file_content) > max_size:
            return Response({"error": "File size exceeds 5MB"}, status=status.HTTP_400_BAD_REQUEST)

        # Upload to S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        object_key = f"invoices/{invoice_id}/uploaded_file"
        try:
            s3_client.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=object_key, Body=file_content)
            if settings.AWS_S3_CUSTOM_DOMAIN:
                uploaded_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{object_key}"
            else:
                uploaded_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{object_key}"
        except Exception as e:
            return Response({"error": f"Failed to upload to S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Update the invoice
        invoice.file_url = uploaded_url
        invoice.save()

        return Response({"message": "File uploaded and invoice updated successfully", "file_url": uploaded_url}, status=status.HTTP_200_OK)


class GetPresignedURLAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PresignedURLSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        filename = serializer.validated_data['filename']
        invoice_id = serializer.validated_data['invoice_id']

        # Check if invoice exists and accessible
        try:
            InvoiceData.objects.get(id=invoice_id, created_by__branch=request.user.branch)
        except InvoiceData.DoesNotExist:
            return Response({"error": "Invoice not found or not accessible"}, status=status.HTTP_404_NOT_FOUND)

        # Generate object key
        object_key = f"invoices/{invoice_id}/{filename}"

        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        try:
            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': object_key,
                    'ContentType': 'application/octet-stream'  # Adjust if needed
                },
                ExpiresIn=300  # 5 minutes
            )
        except NoCredentialsError:
            return Response({"error": "AWS credentials not available"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "presigned_url": presigned_url,
            "object_key": object_key,
            "invoice_id": invoice_id
        }, status=status.HTTP_200_OK)


class UpdateInvoiceFileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateInvoiceFileSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice_id = serializer.validated_data['invoice_id']
        object_key = serializer.validated_data['object_key']

        try:
            invoice = InvoiceData.objects.get(id=invoice_id, created_by__branch=request.user.branch)
        except InvoiceData.DoesNotExist:
            return Response({"error": "Invoice not found or not accessible"}, status=status.HTTP_404_NOT_FOUND)

        # Construct S3 URL
        if settings.AWS_S3_CUSTOM_DOMAIN:
            file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{object_key}"
        else:
            file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{object_key}"

        # Update the invoice
        invoice.file_url = file_url
        invoice.save()

        return Response({"message": "Invoice updated with file URL", "file_url": file_url}, status=status.HTTP_200_OK)