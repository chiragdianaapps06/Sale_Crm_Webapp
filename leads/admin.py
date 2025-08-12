from django.contrib import admin
from .models import Leads
# Register your models here.

# admin.site.register(Leads)

@admin.register(Leads)
class LeadsAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'assigned_to', 'assigned_from')
    list_filter = ('status',)  # This creates filter sidebar for statuses
    search_fields = ('title', 'email')

# admin.site.register(Leads)
