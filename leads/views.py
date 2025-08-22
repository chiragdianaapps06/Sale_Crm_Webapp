from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Leads
from .serializers import LeadSerializer,ReferrerDashboardSerializer
from rest_framework.permissions import IsAuthenticated
from pipelines.choices import PipelineStages
from pipelines.models import Pipeline, PipelineStatus


from django.contrib.auth import get_user_model
User = get_user_model()
# importing logger
from utils.logger import logging


class LeadsViewSet(viewsets.ModelViewSet):
    queryset = Leads.objects.all()  # QuerySet for all Leads
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Leads.objects.all()
        if user.user_type == 'sale':
            return Leads.objects.filter(assigned_to=user)
        if user.user_type == 'ref':
            return Leads.objects.filter(assigned_from=user)
        return Leads.objects.none()


    
    def create(self, request, *args, **kwargs):
        # Extract pipeline name and stage from the request data
        pipeline_name = request.data.get('pipeline_name')
        stage_name = request.data.get('status')
        logging.info(f"pipeline stages are {PipelineStages.values}")
        # if stage_name not in PipelineStages.values:
        #     return Response({"message": "Invalid stage provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate pipeline
        try:
            pipeline_obj = Pipeline.objects.get(name=pipeline_name, user=request.user)
            logging.info(f"pipeline object {pipeline_obj}")
        except Exception as e:
            return Response({
                "message":"Pipeline not found",
                "data":str(e)
            },status=status.HTTP_404_NOT_FOUND)
        
        #status values for the given project
        status_values=pipeline_obj.pipelinestatus_set.all()
        logging.info(f"status values are {status_values}")

        # Get or create the PipelineStatus for the given pipeline and stage
        status_obj = PipelineStatus.objects.filter(pipeline_name=pipeline_obj, stage=stage_name).first()

        if not status_obj:
            # Create a new PipelineStatus if it doesn't exist for the given pipeline
            status_obj = PipelineStatus.objects.create(pipeline_name=pipeline_obj, stage=stage_name)

        # Add the status to the request data
        request_data = request.data.copy()  # Make a mutable copy of request data
        request_data['status'] = status_obj.id

        # Assign the lead to the correct user based on the role of the logged-in user
        user = request.user
        if user.user_type == 'sale':
            # Salesperson should be assigned as "assigned_to"
            request_data['assigned_to'] = user.id

            # Check for duplicates before creating a new lead
            if Leads.objects.filter(assigned_from=request.data.get('assigned_from'), title=request_data.get('title')).exists():
                return Response({
                    "message": f"Lead already assigned by this referrer.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

        elif user.user_type == 'referrer':
            # Referrer should be assigned as "assigned_from"
            request_data['assigned_from'] = user.id

            # Check for duplicates before creating a new lead
            if Leads.objects.filter(assigned_to=request.data.get('assigned_to'), title=request_data.get('title')).exists():
                return Response({
                    "message": f"Lead already assigned to this salesperson.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

        # Now save the lead
        serializer = self.get_serializer(data=request_data)
        
        if serializer.is_valid():
            lead = serializer.save()
            return Response({
                "message": "Lead created successfully.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "message": "Failed to create lead.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing Lead.
        """
        lead = self.get_object()  # Retrieve the object to update
        serializer = self.get_serializer(lead, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Lead updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "message": "Failed to update lead.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a Lead.
        """
        lead = self.get_object()
        lead.delete()
        return Response({
            "message": "Lead deleted successfully."
        }, status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        """
        List all leads.
        """
        leads = self.get_queryset()
        serializer = self.get_serializer(leads, many=True)
        return Response({
            "message": "Leads retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class SalesPersonAllReferrerViewSet(viewsets.ModelViewSet):
    
    queryset = Leads.objects.all()  # QuerySet for all Leads
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    
    def list(self, request):
        """
        Get a list of referrers associated with the logged-in salesperson's leads.
        """
        # Get the logged-in user
        user = request.user

        if user.user_type != 'sale':
            return Response({
                "message": "Only salespeople can view assigned referrers."
            }, status=status.HTTP_403_FORBIDDEN)

        # Get all leads assigned to the logged-in salesperson
        leads_assigned_to_user = Leads.objects.filter(assigned_to=user)

        # Get all referrers associated with the leads assigned to this salesperson
        referrers = User.objects.filter(
            id__in=leads_assigned_to_user.values('assigned_from').distinct()
        )

        # Prepare the response data with referrer details
        referrer_data = []
        for referrer in referrers:
            referrer_leads = leads_assigned_to_user.filter(assigned_from=referrer)

            # Prepare list of leads (title and id) for this referrer
            leads_info = []
            for lead in referrer_leads:
                leads_info.append({
                    "lead_id": lead.id,
                    "title": lead.title
                })
            referrer_data.append({
                "id": referrer.id,
                "username": referrer.username,
                "email": referrer.email,
                "full_name": referrer.get_full_name(),  # Assuming get_full_name() is a method in your CustomUser model
                "lead_assigned":leads_info
            })

        return Response({
            "message": "Referrers associated with the salesperson's leads retrieved successfully.",
            "data": referrer_data
        }, status=status.HTTP_200_OK)


class ReferrerAllSalePersonViewSet(viewsets.ModelViewSet):
    queryset = Leads.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def list(self,request):
    # Get the logged-in user
        user = request.user
    

        if user.user_type != 'ref':
            return Response({
                "message": "Only referrers can view assigned salespeople."
            }, status=status.HTTP_403_FORBIDDEN)

        # Get all leads assigned by the logged-in referrer
        leads_assigned_by_user = Leads.objects.filter(assigned_from=user)

        # Get all salespeople associated with these leads
        salespeople = User.objects.filter(
            id__in=leads_assigned_by_user.values('assigned_to').distinct()
        )

        # Prepare the response data with salesperson details and their associated leads
        salesperson_data = []
        for salesperson in salespeople:
            # Get all leads assigned to this salesperson by the logged-in referrer
            salesperson_leads = leads_assigned_by_user.filter(assigned_to=salesperson)

            # Prepare list of leads (title and id) for this salesperson
            leads_info = []
            for lead in salesperson_leads:
                leads_info.append({
                    "lead_id": lead.id,
                    "title": lead.title
                })

            salesperson_data.append({
                "id": salesperson.id,
                "username": salesperson.username,
                "email": salesperson.email,
                "full_name": salesperson.get_full_name(),  # Assuming get_full_name() is a method in your CustomUser model
                "leads": leads_info  # Adding associated leads
            })

        return Response({
            "message": "Salespeople and their associated leads retrieved successfully.",
            "data": salesperson_data
        }, status=status.HTTP_200_OK)
    

class ReferrerDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        serializer = ReferrerDashboardSerializer(request.user)
        return Response({"status": 200, "message": "Success", "data": serializer.data})

from django.http import JsonResponse
# from .models import PipelineStatus

def get_stages(request):
    pipeline_id = request.GET.get('pipeline_id')
    stages = []
    if pipeline_id:
        stages = list(PipelineStatus.objects.filter(pipeline_name_id=pipeline_id).values('id', 'name'))

    print(stages)
    return JsonResponse(stages, safe=False)
