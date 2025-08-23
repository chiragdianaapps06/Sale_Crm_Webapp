from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .choices import UserType
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django import forms
from leads.models import Leads
from .models import UserDevice

CustomUser = get_user_model()

class CustomUserAdmin(UserAdmin):


    list_display = ('username', 'email', 'is_staff', 'is_superuser','user_type','lead_id', 'lead_title','created_by')
    readonly_fields=['username','email','last_login','date_joined','created_by']

    def get_readonly_fields(self, request, obj = None):
        if obj:
            return ['username','email','last_login','date_joined']
        return ['last_login','date_joined']


    def get_queryset(self, request):

        qs = super().get_queryset(request)
        
        # If the user is a superuser, show all users
        if request.user.is_superuser:
            return qs


        if request.user.user_type == 'sale':
            try:
                # Get leads assigned to the current salesperson
                leads = Leads.objects.filter(assigned_to=request.user)
                referrers = leads.values('assigned_from').distinct()  # Get all referrers assigned to the leads of the logged-in Salesperson
                
                # Combine Referrers from leads with Referrers created by the current Salesperson (created_by)
                referrers_assigned = qs.filter(id__in=referrers)  # Referrers assigned to the Salesperson via leads
                referrers_created = qs.filter(created_by=request.user)  # Referrers created by the Salesperson
                return referrers_assigned | referrers_created  # Combine both sets (OR condition)

            except Exception as e:
                return qs.none()

        # If the logged-in user is a Referrer, get all the Salespeople assigned to their leads
        if request.user.user_type == 'ref':
            leads = Leads.objects.filter(assigned_from=request.user)
            salespeople = leads.values('assigned_to').distinct()  # Get all Salespeople assigned to the leads of the logged-in Referrer
            return qs.filter(id__in=salespeople)  # Only show those Salespeople in the admin list

        return qs.none()  


   
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            fieldsets=super().get_fieldsets(request,obj)
            modified=[]
            for name,dict_ in fieldsets:
                fields=dict_.get("fields",[])
                if 'password' in fields:
                    fields=tuple(f for f in fields if f!='password')
                modified.append((name,{"fields":fields}))

        if obj and obj == request.user and request.user.is_superuser:
            # remove 'user_permissions' from all fieldsets
            new_fieldsets = []
            for name, opts in modified:
                fields = opts.get('fields', [])
                if 'user_permissions' in fields:
                    fields = tuple(f for f in fields if f != 'user_permissions')
                new_fieldsets.append((name, {**opts, 'fields': fields}))
            return new_fieldsets

        return fieldsets

    def lead_id(self, obj):
        # Return the first lead ID associated with this user (referrer or salesperson)
        if obj.user_type == 'sale':
            lead = Leads.objects.filter(assigned_to=obj).first()
        elif obj.user_type == 'ref':
            lead = Leads.objects.filter(assigned_from=obj).first()
        else:
            return None
        return lead.id if lead else None
    
    def lead_title(self, obj):
        # Return the first lead title associated with this user (referrer or salesperson)
        if obj.user_type == 'sale':
            lead = Leads.objects.filter(assigned_to=obj).first()
        elif obj.user_type == 'ref':
            lead = Leads.objects.filter(assigned_from=obj).first()
        else:
            return None
        return lead.title if lead else None
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_superuser','user_type','is_verified'),

        }),
    )


admin.site.register(CustomUser,CustomUserAdmin)


class ReferrerGroupForm(forms.ModelForm):
    referrers = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(user_type=UserType.ref,is_superuser=False),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple("Referrers", is_stacked=False),
    )

    class Meta:
        model = Group
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # editing existing group
            self.fields["referrers"].initial = self.instance.user_set.filter(user_type=UserType.ref,)

    def save(self, commit=True):
        group = super().save(commit=commit)
        if commit:
            group.user_set.set(self.cleaned_data["referrers"])
        return group


class ReferrerGroupAdmin(GroupAdmin):
    form = ReferrerGroupForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if getattr(request.user, "user_type", None) == UserType.sale:
            return qs.filter(name__startswith=f"{request.user.username}_")
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and getattr(request.user, "user_type", None) == UserType.sale:
            obj.name = f"{request.user.username}_{obj.name}"
        super().save_model(request, obj, form, change)


# unregister default and register custom
admin.site.unregister(Group)
admin.site.register(Group, ReferrerGroupAdmin)

admin.site.register(UserDevice)