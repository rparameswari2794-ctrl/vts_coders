# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import User, Developer, Recruiter


# Admin for User (Authentication only)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'role', 'is_verified', 'joined_date']
    list_filter = ['role', 'is_verified']
    search_fields = ['email']
    list_per_page = 25
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'username', 'password', 'role')
        }),
        ('Verification', {
            'fields': ('is_verified',)
        }),
        ('Timestamps', {
            'fields': ('joined_date', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['joined_date', 'last_login']


# Admin for Developers table
@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user_email', 'phone_number', 'skills_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['full_name', 'user__email', 'phone_number', 'skills']
    list_per_page = 25
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'phone_number', 'user')
        }),
        ('Professional Information', {
            'fields': ('bio', 'skills')
        }),
        ('Portfolio', {
            'fields': ('github_url', 'portfolio_url')
        }),
        ('Verification', {
            'fields': ('verification_code',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def skills_preview(self, obj):
        """Show skills as badges"""
        if obj.skills:
            skills_list = obj.skills.split(',')[:3]
            badges = ''.join([f'<span style="background:#e9ecef; padding:2px 8px; border-radius:12px; margin:2px; font-size:11px;">{skill.strip()}</span>' for skill in skills_list])
            if len(obj.skills.split(',')) > 3:
                badges += '<span style="color:#6c757d; font-size:11px;"> +more</span>'
            return format_html(badges)
        return '-'
    skills_preview.short_description = 'Skills'
    
    def save_model(self, request, obj, form, change):
        # Create/Update User automatically
        if not obj.user_id:
            from django.contrib.auth.hashers import make_password
            import random
            import string
            
            # Generate random password for the user
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            user = User.objects.create_user(
                username=obj.full_name.lower().replace(' ', '_') + str(random.randint(100, 999)),
                email=obj.user.email if hasattr(obj, 'user') and obj.user else f"{obj.full_name.lower().replace(' ', '_')}@temp.com",
                password=temp_password,
                role='developer'
            )
            obj.user = user
        super().save_model(request, obj, form, change)


# Admin for Recruiters table
@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user_email', 'company_name', 'company_industry', 'company_location', 'phone_number', 'created_at']
    list_filter = ['company_industry', 'company_size', 'hiring_role_type', 'created_at']
    search_fields = ['full_name', 'user__email', 'company_name', 'company_location', 'phone_number']
    list_per_page = 25
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'phone_number', 'hirer_job_title', 'user')
        }),
        ('Company Information', {
            'fields': ('company_name', 'company_industry', 'company_website', 'company_email', 
                      'company_location', 'company_size', 'company_description')
        }),
        ('Hiring Information', {
            'fields': ('hiring_role_type', 'linkedin_profile_url')
        }),
        ('Verification', {
            'fields': ('verification_code', 'business_proof')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def save_model(self, request, obj, form, change):
        # Create/Update User automatically
        if not obj.user_id:
            from django.contrib.auth.hashers import make_password
            import random
            import string
            
            # Generate random password for the user
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            user = User.objects.create_user(
                username=obj.full_name.lower().replace(' ', '_') + str(random.randint(100, 999)),
                email=obj.company_email if obj.company_email else f"{obj.full_name.lower().replace(' ', '_')}@temp.com",
                password=temp_password,
                role='recruiter'
            )
            obj.user = user
        super().save_model(request, obj, form, change)

