from rest_framework.permissions import  IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView , status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet , mixins
from ivg.models import Branches, InvoiceData, InvoiceUser
from ivg.serializers import BranchSerializer, InvoiceDataListSerializer, InvoiceGenerationSerializer, InvoiceUserSerializer, UltraAdminDashBoardSerializer
from ivg.permissions import UltraAdminPermission 


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