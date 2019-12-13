from django.contrib import admin
# from django.contrib import UserAdmin
from django import forms
from users.models import CustomUser
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    class Meta:
        model = CustomUser
        fields = ('username', 'password')


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'is_staff', 'verified', 'role', 'email')
    list_filter = ('is_staff', 'verified')

    fieldsets = (
        (None, {'fields': ('username',)}),
        (None, {'fields': ('email',)}),
        ('Permissions', {'fields': ('verified', 'role')}),

    )

    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = ()


admin.site.unregister(CustomUser)
admin.site.register(CustomUser, UserAdmin)
