from django.contrib import admin
from .models import Pipeline,PipelineStatus



class PipelineAdmin(admin.ModelAdmin):
    list_display = ['name','user']

admin.site.register(Pipeline,PipelineAdmin)
admin.site.register(PipelineStatus)


