from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .choices import UserType
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django import forms
from leads.models import Leads
from .models import UserDevice
from django.urls import reverse
from django.utils.html import format_html
from Sale_Crm_webapp.admin import admin_site

CustomUser = get_user_model()

class CustomUserAdmin(UserAdmin):


    list_display = ('username','email', 'is_staff', 'is_superuser','user_type','lead_id_link','lead_title_link','created_by_link')
    readonly_fields=['username','email','last_login','date_joined','created_by']
    search_fields = ("username",'created_by__username','lead_title__title')
    list_display_links = ['username','email','lead_id_link','lead_title_link','created_by_link'] 
    

    # @admin.display(description="Username")
    # def username_link(self, obj):
    #     url = reverse("admin:accounts_customuser_change", args=[obj.id])
    #     return format_html('<a href="{}">{}</a>', url, obj.username)
    
    @admin.display(description="Lead ID")
    def lead_id_link(self, obj):
        if obj.user_type == 'sale':
            lead = Leads.objects.filter(assigned_to=obj).first()
        elif obj.user_type == 'ref':
            lead = Leads.objects.filter(assigned_from=obj).first()
        else:
            lead = None

        if lead:
            url = reverse("admin:leads_leads_change", args=[lead.id])  
            return format_html('<a href="{}">{}</a>', url, lead.id)
        return "-"
   
    @admin.display(description="Created By")
    def created_by_link(self, obj):
        if obj.created_by:
            url = reverse("admin:accounts_customuser_change", args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.created_by.username)
        return "-"


    # clickable Lead Title
    @admin.display(description="Lead Title")
    def lead_title_link(self, obj):
        if obj.user_type == 'sale':
            lead = Leads.objects.filter(assigned_to=obj).first()
        elif obj.user_type == 'ref':
            lead = Leads.objects.filter(assigned_from=obj).first()
        else:
            lead = None

        if lead:
            url = reverse("admin:leads_leads_change", args=[lead.id])  
            return format_html('<a href="{}">{}</a>', url, lead.title)
        return "-"

    # def get_list_display(self, request):

    #     if not request.user.is_superuser and  request.user.user_type == "sale" or request.user.user_type == 'ref':
    #         return  ('username', 'email', 'is_staff', 'is_superuser','user_type','lead_id_link','lead_title_link')
    #     return super().get_list_display(request)


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

                # own = 
                return referrers_assigned | referrers_created   # Combine both sets (OR condition)

            except Exception as e:
                return qs.none()

        # If the logged-in user is a Referrer, get all the Salespeople assigned to their leads
        if request.user.user_type == 'ref':
            leads = Leads.objects.filter(assigned_from=request.user)
            salespeople = leads.values('assigned_to').distinct()  # Get all Salespeople assigned to the leads of the logged-in Referrer
            return qs.filter(id__in=salespeople)  # Only show those Salespeople in the admin list

        return qs.none()  


    def get_fieldsets(self, request, obj=None):
            """
            Hide restricted fields from Salesperson in the form.
            """
            fieldsets = super().get_fieldsets(request, obj)
        
            if request.user.is_superuser:
                return fieldsets  

            if request.user.user_type == "sale" and not request.user.is_superuser:
                new_fieldsets = []
                for name, opts in fieldsets:
                    fields = list(opts.get("fields", []))
                    # Remove restricted fields
                    for f in ['is_superuser', 'groups', 'user_permissions', 'is_staff','password']:
                        if f in fields:
                            fields.remove(f)
                    new_fieldsets.append((name, {**opts, "fields": fields}))
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
    def get_form(self, request, obj=None, **kwargs):
        """
        Restrict the creation of Referrer users by Salesperson in the Admin form.
        """
        form = super().get_form(request, obj, **kwargs)

        if request.user.is_superuser:
            return form

        if request.user.user_type == 'sale':
            # If logged-in user is a salesperson, only allow them to create Referrers
            # Ensure 'user_type' is in the form fields
            if 'user_type' in form.base_fields:
                form.base_fields['user_type'].widget.choices = [(x[0], x[1]) for x in form.base_fields['user_type'].choices if x[0] == 'ref']

        return form

    def save_model(self, request, obj, form, change):
        """
        Automatically set created_by = logged-in salesperson when creating a new Referrer.
        Restrict Salesperson so they cannot assign superuser/staff rights.
        """
        is_new = not change  

        if is_new:
            # Salesperson creating a Referrer
            if request.user.is_superuser:
                obj.created_by = request.user
            elif request.user.user_type == "sale" and obj.user_type == "ref":
                obj.created_by = request.user
                obj.is_staff = True

        # First save the object (important: must have an ID before assigning M2M)
        super().save_model(request, obj, form, change)

        # Now handle group assignment safely
        if obj.user_type == "sale":
            from django.contrib.auth.models import Group
            try:
                sale_group = Group.objects.get(name="sale-group")
                user_group = Group.objects.get(name="User")
                obj.groups.set([sale_group, user_group])  # assign both groups
            except Group.DoesNotExist:
                pass  # groups not found, skip
        elif obj.user_type == "ref":
            from django.contrib.auth.models import Group
            try:
                ref_group = Group.objects.get(name="referrer-group")
                obj.groups.set([ref_group])
            except Group.DoesNotExist:
                pass



admin_site.register(CustomUser,CustomUserAdmin)


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
admin_site.unregister(Group)
admin_site.register(Group, ReferrerGroupAdmin)

admin.site.register(UserDevice)


