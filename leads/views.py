from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Leads
from .serializers import LeadSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from pipelines.choices import PipelineStages
from pipelines.models import Pipeline, PipelineStatus

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
        # Extract pipeline name from the request data
        pipeline_name = request.data.get('pipeline_name')
        stage_name = request.data.get('status')
        if stage_name not in PipelineStages.values:
            return Response({"message": "Invalid stage provided."}, status=status.HTTP_400_BAD_REQUEST)


        if pipeline_name:
            # Get or create the pipeline based on the pipeline_name and user
            pipeline_obj, created = Pipeline.objects.get_or_create(name=pipeline_name, user=request.user)
            
            # Get or create the status based on the pipeline object
            # status_obj, created = PipelineStatus.objects.get_or_create(pipeline_name=pipeline_obj, stage=request.data.get("status"))
            status_obj,created = PipelineStatus.objects.get_or_create(pipeline_name=pipeline_obj, stage=request.data.get("status"))
            
            if not status_obj:
                return Response({"message": "No status available for this pipeline."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Add the status to the request data
            request_data = request.data.copy()  # Make a mutable copy of request data
            request_data['status'] = status_obj.id

        # Assign the lead to the correct user based on the role of the logged-in user
        user = request.user
       

        if user.user_type == 'sale':
            # Sale person should be assigned as "assigned_to"
            request_data['assigned_to'] = user.id

            if Leads.objects.filter(assigned_from=request.data.get('assigned_from'), title=request_data.get('title')).exists():
                return Response({
                    "message": f"Lead already assigned by this referrer.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif user.user_type == 'referrer':
            # Referrer should be assigned as "assigned_from"
            request_data['assigned_from'] = user.id

            if Leads.objects.filter(assigned_to=request.data.get('assigned_to'), title=request.data.get('title')).exists():
                return Response({
                    "message": f"Lead already assigned to this salesperson.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
        # Now save the lead
        serializer = LeadSerializer(data=request_data)
        
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

    
