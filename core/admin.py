from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core import models
from django.utils.translation import gettext as _


class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_limited', 'is_partner', 'is_staff',
                            'is_superuser')
                            }),
        # This field is optional
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # May add more user fields like name
            'fields': ('name', 'email', 'password1', 'password2')
        }),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Kollege)
admin.site.register(models.Event)
admin.site.register(models.Persona)
admin.site.register(models.EventReport)
admin.site.register(models.Partner)
admin.site.register(models.Procedure)
admin.site.register(models.GenericGroup)
