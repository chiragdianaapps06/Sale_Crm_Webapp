from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Leads
from .serializers import LeadSerializer,ReferrerDashboardSerializer, LeadSerializer1
from rest_framework.permissions import IsAuthenticated
from pipelines.choices import PipelineStages
from pipelines.models import Pipeline, PipelineStatus
from django.http import JsonResponse

from django.contrib.auth import get_user_model
User = get_user_model()
# importing logger
from utils.logger import logging

# push notifications library import
from .notifications import send_push_notification
from accounts.models import UserDevice

class LeadsViewSet(viewsets.ModelViewSet):
    queryset = Leads.objects.all()  # QuerySet for all Leads
    serializer_class = LeadSerializer1
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
        pipeline_name = request.data.get('pipeline_name')
        stage_name = request.data.get('status')
        assigned_from = request.data.get('assigned_from')

        user = request.user
        logging.info(user.user_type)
        if user.user_type == 'sale':
            # Salesperson logic: Ensure that a pipeline name is provided
            if not pipeline_name:
                logging.info(pipeline_name)
                return Response({
                    "message": "Pipeline name is required for salesperson.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the pipeline already exists for the salesperson
            try:
                pipeline_obj = Pipeline.objects.get(name=pipeline_name, owner_id=request.user)
                logging.info("-------------",pipeline_obj)
                logging.info(f"Pipeline found for salesperson: {pipeline_obj}")
            except Pipeline.DoesNotExist:
                # If the pipeline doesn't exist, create it
                pipeline_obj = Pipeline.objects.create(
                    name=pipeline_name,
                    owner=request.user,  # Set the owner to the salesperson
                    user=User.objects.get(id=assigned_from)
                )
                logging.info(f"Created new pipeline for salesperson: {pipeline_obj}")
            
            # Create the status for the given pipeline and stage
            if stage_name:
                status_obj = PipelineStatus.objects.filter(pipeline_name=pipeline_obj, stage=stage_name).first()
                if not status_obj:
                    # Create a new status if it doesn't exist for the given pipeline and stage
                    status_obj = PipelineStatus.objects.create(pipeline_name=pipeline_obj, stage=stage_name)
                    logging.info(f"Created new status: {status_obj}")
            else:
                status_obj = None  # If no stage_name is provided, set status to None


            


        elif user.user_type == 'ref':
            # Referrer logic: Only associate with an existing pipeline, no creation
            if pipeline_name:
                # If a pipeline_name is passed, fetch the corresponding pipeline for the user
                try:
                    pipeline_obj = Pipeline.objects.get(name=pipeline_name, user=request.user)
                    logging.info(f"Pipeline found for referrer: {pipeline_obj}")
                    
                    # Fetch the pipeline status based on the provided stage_name
                    if stage_name:
                        status_obj = PipelineStatus.objects.filter(pipeline_name=pipeline_obj, stage=stage_name).first()
                        if not status_obj:
                            logging.info(f"Status not found for stage {stage_name}. Setting status to None.")
                            status_obj = None
                    else:
                        logging.info(f"No stage provided, setting status to None.")
                        status_obj = None
                except Pipeline.DoesNotExist:
                    return Response({
                        "message": "Pipeline not found",
                        "data": "The pipeline does not exist for this user."
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # If no pipeline_name is provided, set both pipeline_name and status to None
                pipeline_obj = None
                status_obj = None
                logging.info(f"Referrer did not provide a pipeline name. Setting pipeline_name and status to None.")

        else:
            return Response({
                "message": "Permission denied",
                "data": "User does not have permission to create leads."
            }, status=status.HTTP_403_FORBIDDEN)

        # Add the status to the request data
        request_data = request.data.copy()  # Make a mutable copy of request data
        logging.info( status_obj)

        if pipeline_obj:
            request_data['lead_pipeline'] = pipeline_obj.id
        else:
            request_data['lead_pipeline'] = None
        if status_obj:
            request_data['status'] = status_obj.id
        else:
            request_data['status'] = None

        # Assign the lead to the correct user based on the role of the logged-in user
        if user.user_type == 'sale':
            # Salesperson should be assigned as "assigned_to"
            request_data['assigned_to'] = user.id
        elif user.user_type == 'ref':
            # Referrer should be assigned as "assigned_from"
            request_data['assigned_from'] = user.id

        # Check for duplicates before creating a new lead
        if Leads.objects.filter(assigned_from=request.data.get('assigned_from'), title=request_data.get('title')).exists():
            return Response({
                "message": f"Lead already assigned by this referrer.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Now save the lead
        serializer = self.get_serializer(data=request_data)
        
        if serializer.is_valid():
            lead = serializer.save()

            
            try:
                referrer = User.objects.get(id=assigned_from)
                user_device = UserDevice.objects.get(user=referrer)  # Fetch the referrer's device token
                send_push_notification(user_device.device_token, 
                                    "Lead Updated", 
                                    f"The lead you referred '{request.data.get('title')}' has been updated by the salesperson.")
            except UserDevice.DoesNotExist:
                logging.info(f"No device token found for referrer {referrer.username}")

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
        user = request.user
        assigned_from_user = request.data.get("assinged_from",lead.assigned_from)
      
        
        # Extract pipeline_name and status (as strings) from the request
        pipeline_name = request.data.get('pipeline_name', '')
        stage_name = request.data.get('status', '')  # The stage name as a string

        # If the user is a referrer, prevent them from updating the pipeline or status
        if user.user_type == 'ref':
            return Response({
                "message": "Referrers cannot update pipeline or status. They can only create leads with null pipeline_name and status."
            }, status=status.HTTP_403_FORBIDDEN)

        # If both pipeline_name and status are provided
        if pipeline_name:
            # If no pipeline is associated with the lead, create a new one
            if not lead.lead_pipeline:
                try:
                    # Try to find the pipeline for the current user
                    pipeline_obj = Pipeline.objects.get(name=pipeline_name, owner=user)
                except Pipeline.DoesNotExist:
                    # If the pipeline does not exist, create a new pipeline
                    pipeline_obj = Pipeline.objects.create(
                        name=pipeline_name,
                        user=assigned_from_user ,# Set the current user as the owner of the pipeline
                        owner=user   # Owner is the same as user in this case
                    )
                lead.lead_pipeline = pipeline_obj  # Assign the new or found pipeline to the lead
                logging.info(f"New pipeline assigned to lead: {pipeline_obj}")

            # Handle the status for the given pipeline and stage
            if stage_name:
                # Check if the status already exists for the pipeline and stage
                status_obj = PipelineStatus.objects.filter(pipeline_name=lead.lead_pipeline, stage=stage_name).first()
                if status_obj:
                    # If the status exists, assign it to the lead
                    lead.status = status_obj
                    logging.info(f"Using existing status: {status_obj}")
                else:
                    # If the status does not exist, create it
                    status_obj = PipelineStatus.objects.create(pipeline_name=lead.lead_pipeline, stage=stage_name)
                    lead.status = status_obj
                    logging.info(f"Created new status for pipeline {lead.lead_pipeline}: {status_obj}")
            else:
                # If no stage_name is provided, we can either set status to None or use the existing one
                status_obj = lead.status  # Keep the existing status
                logging.info(f"Status remains unchanged for lead: {status_obj}")
        else:
            # If no pipeline_name is provided, use the current pipeline and status
            logging.info("No pipeline name provided, using the current pipeline and status for lead.")
            status_obj = lead.status  # Keep the existing status

        # If only status is provided, update the existing pipeline's status
        if stage_name:
            # Ensure that the lead has a pipeline and that the new status exists
            if lead.lead_pipeline:
                status_obj = PipelineStatus.objects.filter(pipeline_name=lead.lead_pipeline, stage=stage_name).first()
                if status_obj:
                    # If the status exists, update the lead's status
                    lead.status = status_obj
                    logging.info(f"Status updated for pipeline {lead.lead_pipeline}: {status_obj}")
                else:
                    # If the status doesn't exist, create a new status for the pipeline
                    status_obj = PipelineStatus.objects.create(pipeline_name=lead.lead_pipeline, stage=stage_name)
                    lead.status = status_obj
                    logging.info(f"Created new status for pipeline {lead.lead_pipeline}: {status_obj}")

        # Assign the status to the lead
        lead.status = status_obj

        # Assign the lead to the correct user based on the role of the logged-in user
        if user.user_type == 'sale':
            lead.assigned_to = user  # Salesperson should be assigned as "assigned_to"
        elif user.user_type == 'ref':
            lead.assigned_from = user  # Referrer should be assigned as "assigned_from"
        

        #  push notification funcanality
        if lead.assigned_from:
            referrer = lead.assigned_from
            try:
                user_device = UserDevice.objects.get(user=referrer)  # Get referrer’s device token
                send_push_notification(user_device.device_token, 
                                    "Lead Updated", 
                                    f"The lead you referred '{lead.title}' has been updated by the salesperson.")
            except UserDevice.DoesNotExist:
                logging.info(f"No device token found for referrer {referrer.username}")

        # Save the updated lead
        serializer = self.get_serializer(lead, data=request.data, partial=True)

        if serializer.is_valid():
            lead = serializer.save()
            return Response({
                "message": "Lead updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Failed to update lead.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


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



def get_stages(request):
    pipeline_id = request.GET.get('pipeline_id')
    stages = []
    if pipeline_id:
        stages = list(PipelineStatus.objects.filter(pipeline_name_id=pipeline_id).values('id', 'name'))

    logging.info(stages)
    return JsonResponse(stages, safe=False)
