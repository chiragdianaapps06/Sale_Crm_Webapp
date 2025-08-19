from django.contrib import admin
from .models import Leads
from django.contrib.auth import get_user_model
User = get_user_model()

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
        return queryset
    

class LeadsAdmin(admin.ModelAdmin):
    list_display = ['title', 'email', 'assigned_from', 'assigned_to', 'status']
    # list_filter = ['status', 'assigned_to', 'assigned_from']
    list_filter = ['status', AssignedFromFilter ,AssignedToFilter]

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
        # Customizing filter choices in admin
        # from .models import User  # or wherever your User model is
        
        if db_field.name == "assigned_from":
            if request.user.is_superuser or request.user.user_type == 'sale':
                # only show referrers
                kwargs["queryset"] = User.objects.filter(user_type='ref')
            
            elif request.user.user_type == 'ref':
                # show only themselves
                kwargs["queryset"] = User.objects.filter(pk=request.user.pk)

        if db_field.name == "assigned_to":
            if request.user.is_superuser:
                kwargs["queryset"] = User.objects.filter(user_type='sale')
            elif request.user.user_type == 'sale':
                kwargs["queryset"] = User.objects.filter(pk=request.user.pk)
            elif request.user.user_type == 'ref':
                # show all salespeople
                kwargs["queryset"] = User.objects.filter(user_type='sale')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Leads, LeadsAdmin)
