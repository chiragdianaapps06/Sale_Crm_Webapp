from rest_framework import serializers
from .models import Pipeline,PipelineStatus
from django.db import transaction
from utils.logger import logging

class PipelineStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model=PipelineStatus
        fields=['stage']

class PipelineSerializer(serializers.ModelSerializer):
    status=PipelineStatusSerializer(many=True)

    class Meta:
        model=Pipeline
        fields=['name','user',"status"]
        read_only_fields=['user']
    
    def to_internal_value(self, data):
        status_data=data.get('status')
        if status_data and all([isinstance(status,str) for status in status_data]):
            data=data.copy()
            data["status"]=[{"stage":status} for status in status_data]
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self,validated_data):
        validated_data['user']=self.context.get('request').user
        status_data=validated_data.pop('status',None)

        logging.info(f"status data is {status_data}")

        pipeline=Pipeline.objects.create(**validated_data)
        logging.info(f"Pipeline created successfully.{pipeline}")
        for status in status_data:
            obj,created= PipelineStatus.objects.get_or_create(pipeline_name=pipeline,**status)
            if created:
                logging.info(f"Pipeline status created successfully. status = {status}")
            else:
                logging.info(f"Pipeline status created skipped. status = {status}")
      
        return pipeline