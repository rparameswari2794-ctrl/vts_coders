from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project, Developer

@receiver(post_save, sender=Project)
def update_developer_project_count(sender, instance, **kwargs):
    """Auto-increment project count when project is approved"""
    if instance.status == 'approved':
        developer = instance.developer
        # Count all approved projects (including the new one)
        developer.project_count = developer.projects.filter(status='approved').count()
        developer.save()
        print(f"Project count updated to: {developer.project_count}")

@receiver(post_save, sender=Developer)
def ensure_default_values(sender, instance, created, **kwargs):
    """Ensure default values are set when developer is created"""
    if created:
        if instance.project_count == 0:
            instance.project_count = 42
        if instance.follower_count == 0:
            instance.follower_count = 58
        if instance.total_views == 0:
            instance.total_views = 120
        instance.save()