from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin


CustomUser = get_user_model()

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser','user_type')

    
    readonly_fields = ('email','date_joined','last_login')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2','is_staff', 'is_superuser','user_type'),
        }),
    )


admin.site.register(CustomUser,CustomUserAdmin)

