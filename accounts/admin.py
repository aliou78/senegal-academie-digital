from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, InstructorProfile, EnterpriseProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Administration des utilisateurs
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Informations personnelles'), {
            'fields': ('role', 'phone', 'date_of_birth', 'gender', 'profile_picture', 'bio', 'location', 'preferred_language', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Informations personnelles'), {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Administration des profils utilisateurs
    """
    list_display = ('user', 'get_skills_count', 'get_experience_count')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    
    def get_skills_count(self, obj):
        return len(obj.skills) if obj.skills else 0
    get_skills_count.short_description = 'Nombre de compétences'
    
    def get_experience_count(self, obj):
        return len(obj.experience) if obj.experience else 0
    get_experience_count.short_description = 'Nombre d\'expériences'


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    """
    Administration des profils formateurs
    """
    list_display = ('user', 'title', 'company', 'years_of_experience', 'hourly_rate', 'is_approved')
    list_filter = ('is_approved', 'years_of_experience')
    search_fields = ('user__username', 'user__email', 'title', 'company')
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('user', 'title', 'company', 'years_of_experience')
        }),
        (_('Spécialisations et tarifs'), {
            'fields': ('specializations', 'hourly_rate', 'availability')
        }),
        (_('Statut'), {
            'fields': ('is_approved', 'approval_date')
        }),
    )


@admin.register(EnterpriseProfile)
class EnterpriseProfileAdmin(admin.ModelAdmin):
    """
    Administration des profils entreprises
    """
    list_display = ('company_name', 'company_type', 'industry', 'company_size', 'contact_person')
    list_filter = ('company_type', 'industry', 'company_size')
    search_fields = ('company_name', 'contact_person', 'user__email')
    
    fieldsets = (
        (_('Informations de l\'entreprise'), {
            'fields': ('user', 'company_name', 'company_type', 'industry', 'company_size', 'website', 'description')
        }),
        (_('Contact'), {
            'fields': ('contact_person', 'contact_phone')
        }),
    )
