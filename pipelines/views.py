from django.shortcuts import render
from rest_framework.views  import APIView
from rest_framework.response import Response
from rest_framework import status,viewsets
from .serializers import PipelineSerializer,PipelineStatusSerializer
from utils.logger import logging
from rest_framework.permissions import IsAuthenticated
from .models import Pipeline,PipelineStatus

class PipelineCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        try:
            if request.user.user_type=="referrer":
                return Response({
                    'data':'None'
                },status=status.HTTP_403_FORBIDDEN)

            serializer=PipelineSerializer(data=request.data,context={'request':request})

            if serializer.is_valid():
                pipeline=serializer.save()
                logging.info(f"pipeline created successfully. id = {pipeline.id}")
                return Response({
                    'message':'pipeline created successfully',
                    'data':serializer.validated_data
                },status=status.HTTP_201_CREATED)
            return Response({ 
                            'data':serializer.errors
                            },status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({ 
                            'message': 'error',
                            'data':str(e)
                            },status=status.HTTP_400_BAD_REQUEST)
        

class PipelineStatusViewset(viewsets.ModelViewSet):
    serializer_class=PipelineStatusSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        queryset=PipelineStatus.objects.filter(pipeline_name__user=self.request.user)
        pipeline_id=self.request.query_params.get("pipeline_id")
        if pipeline_id:
            queryset=queryset.filter(pipeline_name_id=pipeline_id)
        return queryset
    

    def create(self, request, *args, **kwargs):
        pipeline_id = request.query_params.get("pipeline_id")

        if not pipeline_id:
            return Response({"message": "pipeline_id is required","data":None}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pipeline = Pipeline.objects.get(id=pipeline_id, user=request.user)
        except Pipeline.DoesNotExist:
            return Response({"message": "Pipeline not found","data":None}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stage = serializer.validated_data.get("stage")

        # prevent duplicate status for the same pipeline
        if PipelineStatus.objects.filter(pipeline_name=pipeline, stage=stage).exists():
            return Response(
                {"message": f"Status '{stage}' already exists for this pipeline","data":None},
                status=status.HTTP_400_BAD_REQUEST
            )

        status_obj = PipelineStatus.objects.create(pipeline_name=pipeline, **serializer.validated_data)

        return Response(
            self.get_serializer(status_obj).data,
            status=status.HTTP_201_CREATED
        )


    def update(self, request, *args, **kwargs):
        pipeline_id = request.query_params.get("pipeline_id")
        status_id = kwargs.get("pk")  # taken from /status/<status_id>/

        if not pipeline_id:
            return Response({"message": "pipeline_id is required",'data':None}, status=400)
        try:
            status_obj = PipelineStatus.objects.get(
                id=status_id,
                pipeline_name_id=pipeline_id,
                pipeline_name__user=request.user
            )
        except PipelineStatus.DoesNotExist:
            return Response({"message": "Status not found for this pipeline","data":None}, status=status.HTTP_404_NOT_FOUND)
        
        new_stage = request.data.get("stage")
        if new_stage:
            # check for duplicate stage in same pipeline (excluding self)
            exists = PipelineStatus.objects.filter(
                pipeline_name_id=pipeline_id,
                stage=new_stage
            ).exclude(id=status_id).exists()

            if exists:
                return Response(
                    {"message": f"Stage '{new_stage}' already exists in this pipeline","data":None},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(status_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'data':serializer.data
        },
        status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        pipeline_id = request.query_params.get("pipeline_id")
        status_id = kwargs.get("pk")  # taken from /status/<status_id>/

        if not pipeline_id:
            return Response({"message": "pipeline_id is required",'data':None}, status=status.HTTP_400_BAD_REQUEST)

        try:
            status_obj = PipelineStatus.objects.get(
                id=status_id,
                pipeline_name_id=pipeline_id,
                pipeline_name__user=request.user
            )
        except PipelineStatus.DoesNotExist:
            return Response({"data": "Status not found for this pipeline","data":None}, status=status.HTTP_400_BAD_REQUEST)
        
        
        status_obj.delete()
        return Response({
            "data":None
        },status=status.HTTP_200_OK)