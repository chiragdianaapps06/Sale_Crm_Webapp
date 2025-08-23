from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Pipeline, PipelineStatus
from leads.models import Leads
User = get_user_model()
from django.core.exceptions import ValidationError


from django.db.models import Q

class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'owner']

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Superuser can see all pipelines
        if request.user.is_superuser:
            return qs

        # Salesperson can only see pipelines they created
        elif request.user.user_type == 'sale':
            return qs.filter(owner=request.user)  # Salesperson can only see pipelines created by them

        # Referrer can only see pipelines created by them (user)
        elif request.user.user_type == 'ref':
            return qs.filter(user=request.user)  # Show pipelines owned by the referrer

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            # Salesperson should only be able to assign a referrer they created or are associated with
            if request.user.user_type == 'sale':
                # Referrers created by the salesperson or those associated through leads
                referrers = User.objects.filter(
                    Q(user_type='ref') & Q(leads_referrar__assigned_to=request.user)
                ).distinct()

                # Referrers created by the salesperson
                referrers_created_by_salesperson = User.objects.filter(
                    created_by=request.user, 
                    user_type='ref'
                ).distinct()

                # Use Q objects to combine both sets of referrers
                referrers = referrers | referrers_created_by_salesperson
                kwargs['queryset'] = referrers
            elif request.user.user_type == 'ref':
                # Referrers can only see their own entry
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk)
        elif db_field.name == 'owner':
            # Salesperson can only see their own name as owner
            if request.user.user_type == 'sale':
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Ensure uniqueness of the pipeline name for the referrer (user)
        if not change:  # Only on creation
            if Pipeline.objects.filter(name=obj.name, user=obj.user).exists():
                raise ValidationError(f"A pipeline with this name already exists for the referrer {obj.user}.")
            obj.owner = request.user  # Set the owner as the logged-in salesperson

        super().save_model(request, obj, form, change)


class PipelineStatusAdmin(admin.ModelAdmin):
    # form = PipelineStatusForm
    list_display = ['pipeline_name', 'stage']

    def get_form(self, request, obj=None, **kwargs):
        # Customize the form for 'PipelineStatus'
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['pipeline_name'].queryset = Pipeline.objects.filter(owner=request.user)

        # If the user is a salesperson, they can only see their own pipelines
        if request.user.user_type == 'sale':
            form.base_fields['pipeline_name'].queryset = form.base_fields['pipeline_name'].queryset.filter(owner=request.user)

        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        # Filter by user's pipelines (salesperson or referrer)
        if request.user.user_type == 'sale':
            return qs.filter(pipeline_name__owner=request.user)
        elif request.user.user_type == 'ref':
            return qs.filter(pipeline_name__user=request.user)

        return qs.none()




# Register the models with the updated admin classes
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(PipelineStatus, PipelineStatusAdmin)
