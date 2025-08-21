from rest_framework import serializers
from .models import Leads
from pipelines.models import PipelineStatus
from django.contrib.auth import get_user_model\

User = get_user_model()

# class LeadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Leads
#         fields = ['id','title', 'email', 'description', 'assigned_from', 'assigned_to', 'status']

#     def validate(self, attrs):
      
#         pipeline_name = attrs.get('pipeline_name')
#         if pipeline_name:
#             status = PipelineStatus.objects.filter(pipeline_name=pipeline_name).first()
#             if not status:
#                 raise serializers.ValidationError("No status found for this pipeline.")
#             attrs['status'] = status  # Set default status from the pipeline
#         return attrs



class LeadSerializer(serializers.ModelSerializer):
    # Include the assigned_from (Referrer) and assigned_to (Sales Person) details
    assigned_from = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    # Adding a list of referrers for Sales Person view
    referrers = serializers.SerializerMethodField()

    class Meta:
        model = Leads
        fields = ['id', 'title', 'email', 'description', 'assigned_from', 'assigned_to', 'status', 'referrers']

    def get_referrers(self, obj):
        # Fetch all referrers for the given lead

        return obj.assigned_from.username 
    
    def validate(self, attrs):
      
        pipeline_name = attrs.get('pipeline_name')
        if pipeline_name:
            status = PipelineStatus.objects.filter(pipeline_name=pipeline_name).first()
            if not status:
                raise serializers.ValidationError("No status found for this pipeline.")
            attrs['status'] = status  # Set default status from the pipeline
        return attrs