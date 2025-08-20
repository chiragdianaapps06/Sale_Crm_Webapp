from rest_framework import serializers
from .models import Leads
from pipelines.models import PipelineStatus

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        fields = ['id','title', 'email', 'description', 'assigned_from', 'assigned_to', 'status']

    def validate(self, attrs):
      
        pipeline_name = attrs.get('pipeline_name')
        if pipeline_name:
            status = PipelineStatus.objects.filter(pipeline_name=pipeline_name).first()
            if not status:
                raise serializers.ValidationError("No status found for this pipeline.")
            attrs['status'] = status  # Set default status from the pipeline
        return attrs
