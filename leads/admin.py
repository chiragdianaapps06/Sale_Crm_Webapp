from django.contrib import admin
from .models import Leads
from django.contrib.auth import get_user_model
User = get_user_model()
from utils.logger import logging
from accounts.choices import UserType

from django import forms
from pipelines.models import PipelineStatus , Pipeline

class AssignedFromFilter(admin.SimpleListFilter):
    title = 'assigned from'
    parameter_name = 'assigned_from'

    def lookups(self, request, model_admin):
        # For superusers and sale: all referrer users
        if request.user.is_superuser or request.user.user_type == 'sale':
            referrers = User.objects.filter(user_type='ref')
            return [(user.pk, str(user)) for user in referrers]
        # For referrer: only themselves
        elif request.user.user_type == 'ref':
            return [(request.user.pk, str(request.user))]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(assigned_from__pk=self.value())
        return queryset

# Custom admin filter for assigned_to
class AssignedToFilter(admin.SimpleListFilter):
    title = 'assigned to'
    parameter_name = 'assigned_to'

    def lookups(self, request, model_admin):
        # For superuser: all salespeople
        if request.user.is_superuser:
            sales = User.objects.filter(user_type='sale')
            return [(user.pk, str(user)) for user in sales]
        # For sale: only themselves
        elif request.user.user_type == 'sale':
            return [(request.user.pk, str(request.user))]
        # For referrer: all salespeople
        elif request.user.user_type == 'ref':
            sales = User.objects.filter(user_type='sale')
            return [(user.pk, str(user)) for user in sales]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(assigned_to__pk=self.value())
#         return queryset
# class LeadsAdminForm(forms.ModelForm):
#     class Meta:
#         model = Leads
#         fields = '__all__'

#     def __init__(self, *args, **kwargs):
#         super(LeadsAdminForm, self).__init__(*args, **kwargs)
#         # If we have a pipeline selected, filter available pipeline statuses
#         if 'pipeline_name' in self.initial:
#             pipeline = self.initial['pipeline_name']
#             self.fields['status'].queryset = PipelineStatus.objects.filter(pipeline_name=pipeline)

#     # Dynamically update available status based on selected pipeline
#     def clean(self):
#         cleaned_data = super().clean()
#         pipeline = cleaned_data.get("pipeline_name")
#         if pipeline:
#             cleaned_data['status'] = PipelineStatus.objects.filter(pipeline_name=pipeline).first()  # Get default status or first status
#         return cleaned_data



from django import forms
# from .models import Leads, PipelineStaged, Pipelines
class LeadsAdminForm(forms.ModelForm):
    pipeline = forms.ModelChoiceField(
        queryset=Pipeline.objects.all(),
        required=False,
        label="Pipeline"
    )

    class Meta:
        model = Leads
        fields = ['title', 'email', 'assigned_from', 'assigned_to','pipeline', 'status']  # Explicit field order

    def __init__(self, *args, **kwargs):
        super(LeadsAdminForm, self).__init__(*args, **kwargs)

        # Ensure the 'status' field exists before trying to filter its queryset
        if 'status' in self.fields:
            # Initially set queryset for the 'status' field to none
            self.fields['status'].queryset = PipelineStatus.objects.none()

            # If a 'pipeline' is passed to the form, filter the 'status' field accordingly
            if 'pipeline' in self.initial:
                pipeline = self.initial['pipeline']
                self.fields['status'].queryset = PipelineStatus.objects.filter(pipeline_name=pipeline)

            # If a 'pipeline' is selected in the form during `POST`, filter 'status' based on that
            if 'pipeline' in self.data:
                pipeline_id = self.data.get('pipeline')
                if pipeline_id:
                    pipeline = Pipeline.objects.get(id=pipeline_id)
                    self.fields['status'].queryset = PipelineStatus.objects.filter(pipeline_name=pipeline)

    def clean(self):
        cleaned_data = super().clean()
        pipeline = cleaned_data.get("pipeline")
        status = cleaned_data.get("status")

        # If pipeline is selected, filter status based on pipeline
        if pipeline:
            cleaned_data['status'] = PipelineStatus.objects.filter(pipeline_name=pipeline).first()  # Default to first status for pipeline
        
        return cleaned_data



class LeadsAdmin(admin.ModelAdmin):
    form = LeadsAdminForm
    list_display = ['title', 'email', 'assigned_from', 'assigned_to', 'status']  # Don't display pipeline_name
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.user_type == 'sale':
            return qs.filter(assigned_to=request.user)
        elif request.user.user_type == 'ref':
            return qs.filter(assigned_from=request.user)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Custom filter for foreign key fields
        if db_field.name == 'assigned_from':
            if request.user.is_superuser or request.user.user_type == 'sale':
                kwargs['queryset'] = User.objects.filter(user_type='ref')
            elif request.user.user_type == 'ref':
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk)

        if db_field.name == 'assigned_to':
            if request.user.is_superuser:
                kwargs['queryset'] = User.objects.filter(user_type='sale')
            elif request.user.user_type == 'sale':
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk)
            elif request.user.user_type == 'ref':
                kwargs['queryset'] = User.objects.filter(user_type='sale')

        if db_field.name == 'status':
            pipeline = request.GET.get('pipeline_name')  # Get pipeline from query params
            if pipeline:
                kwargs['queryset'] = PipelineStatus.objects.filter(pipeline_name=pipeline)
            else:
                kwargs['queryset'] = PipelineStatus.objects.none()  # If no pipeline, no status options

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Leads, LeadsAdmin)
