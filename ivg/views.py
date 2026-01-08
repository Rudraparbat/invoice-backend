from rest_framework.permissions import  IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet , mixins
from ivg.models import InvoiceData
from ivg.serializers import InvoiceDataListSerializer, InvoiceGenerationSerializer



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