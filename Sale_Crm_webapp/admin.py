from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group

class CustomAdminSite(AdminSite):
    login_template='admin/login.html'
   

admin_site=CustomAdminSite()
admin_site.register(Group)
