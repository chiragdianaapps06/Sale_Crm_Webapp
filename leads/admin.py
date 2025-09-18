from django.contrib import admin
from .models import Leads
from django.contrib.auth import get_user_model
User = get_user_model()
from utils.logger import logging
from accounts.choices import UserType
from pipelines.models import PipelineStatus , Pipeline
from Sale_Crm_webapp.admin import admin_site


# Custom Admin filter for 'Assigned From' (Referrer)
class AssignedFromFilter(admin.SimpleListFilter):
    title = 'Assigned from'
    parameter_name = 'assigned_from'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            referrers = User.objects.filter(user_type='ref')
            return [(user.pk, str(user)) for user in referrers]
        elif request.user.user_type == 'sale':
            # Only referrers assigned to this salesperson or created by them
            referrers = User.objects.filter(
                user_type='ref',
                leads_referrar__assigned_to=request.user
            ).distinct()

            referrers_created_by_salesperson = User.objects.filter(
                created_by=request.user,
                user_type='ref'
            ).distinct()

            # Combine both sets
            referrers = referrers.union(referrers_created_by_salesperson)
            return [(user.pk, str(user)) for user in referrers]
        elif request.user.user_type == 'ref':
            return [(request.user.pk, str(request.user))]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(assigned_from__pk=self.value())
        return queryset

# Custom Admin filter for 'Assigned To' (Salesperson)
class AssignedToFilter(admin.SimpleListFilter):
    title = 'Assigned to'
    parameter_name = 'assigned_to'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            salespeople = User.objects.filter(user_type='sale')
            return [(user.pk, str(user)) for user in salespeople]
        elif request.user.user_type == 'sale':
            return [(request.user.pk, str(request.user))]
        elif request.user.user_type == 'ref':
            salespeople = User.objects.filter(
                user_type='sale', 
                leads_sales__assigned_from=request.user
            ).distinct()

            salespeople_created_by_referrer = User.objects.filter(
                created_by=request.user,
                user_type='sale'
            ).distinct()

            salespeople = salespeople.union(salespeople_created_by_referrer)
            return [(user.pk, str(user)) for user in salespeople]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(assigned_to__pk=self.value())
        return queryset


class LeadsAdmin(admin.ModelAdmin):
   
    list_display = ['title', 'email', 'description', 'assigned_from', 'assigned_to', 'lead_pipeline', 'status']
    # list_filter = [AssignedFromFilter,AssignedToFilter]
    list_display_links = ['email','lead_pipeline']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kwargs['queryset'] = PipelineStatus.objects.none()        

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.user_type == 'sale':
            return qs.filter(assigned_to=request.user)
        elif request.user.user_type == 'ref':
            return qs.filter(assigned_from=request.user)
        return qs.none()

    def get_list_filter(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            return [AssignedFromFilter, AssignedToFilter]
        elif request.user.is_authenticated and request.user.user_type == 'sale':
            return [AssignedFromFilter]
        elif request.user.is_authenticated and request.user.user_type == 'ref':
            return [AssignedToFilter]


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
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


        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    class Media:
        js = ('admin/js/lead_admin.js',)

admin_site.register(Leads, LeadsAdmin)


