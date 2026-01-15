from rest_framework.permissions import  IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView , status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet , mixins
from ivg.models import Branches, InvoiceData, InvoiceUser
from ivg.serializers import BranchSerializer, InvoiceDataListSerializer, InvoiceGenerationSerializer, InvoiceUserSerializer, UltraAdminDashBoardSerializer, PresignedURLSerializer, UpdateInvoiceFileSerializer, ListInvoiceFilesSerializer, InvoiceViewFileSerializer
from ivg.permissions import UltraAdminPermission, CoOfficerPermission
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
                ExpiresIn=3000  # 5 minutes
            )
        except NoCredentialsError:
            return Response({"error": "AWS credentials not available"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "presigned_url": presigned_url,
            "object_key": object_key,
            "invoice_id": invoice_id
        }, status=status.HTTP_200_OK)


class UpdateInvoiceFileAPIView(APIView):
    permission_classes = [IsAuthenticated, CoOfficerPermission]
    serializer_class = UpdateInvoiceFileSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        invoice_id = serializer.validated_data['invoice_id']
        object_key = serializer.validated_data['object_key']

        try:
            # Fetch the specific invoice
            invoice = InvoiceData.objects.get(
                id=invoice_id, 
                created_by__branch=request.user.branch
            )
        except InvoiceData.DoesNotExist:
            return Response(
                {"error": "Invoice not found or not accessible"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # SAVE ACTION: Store the permanent object key only
        invoice.object_key = object_key
        invoice.save()

        return Response({
            "message": "Invoice updated successfully", 
            "invoice_id": invoice_id,
            "object_key": object_key
        }, status=status.HTTP_200_OK)

class ListInvoiceFilesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListInvoiceFilesSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice_id = serializer.validated_data['invoice_id']

        # Check if invoice exists and accessible
        try:
            InvoiceData.objects.get(id=invoice_id, created_by__branch=request.user.branch)
        except InvoiceData.DoesNotExist:
            return Response({"error": "Invoice not found or not accessible"}, status=status.HTTP_404_NOT_FOUND)

        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        prefix = f"invoices/{invoice_id}/"
        try:
            response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix)
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Generate presigned GET URL for private bucket
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': obj['Key']},
                        ExpiresIn=3600  # 1 hour
                    )
                    files.append({
                        "key": obj['Key'],
                        "presigned_url": presigned_url,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat()
                    })
        except Exception as e:
            return Response({"error": f"Failed to list files: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"files": files}, status=status.HTTP_200_OK)
    
class GetInvoiceViewURLAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceViewFileSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice_id = serializer.validated_data['invoice_id']

        try:
            invoice = InvoiceData.objects.get(
                id=invoice_id,
                created_by__branch=request.user.branch
            )
        except InvoiceData.DoesNotExist:
            return Response(
                {"error": "Invoice not found or not accessible"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not invoice.object_key:
            return Response(
                {"error": "No file attached to this invoice"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        try:
            view_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': invoice.object_key
                },
                ExpiresIn=300  # 5 minutes
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to generate view URL: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "success": True,
                "invoice_id": invoice_id,
                "view_url": view_url
            },
            status=status.HTTP_200_OK
        )
