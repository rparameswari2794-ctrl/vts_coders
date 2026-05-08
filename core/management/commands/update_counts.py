from django.core.management.base import BaseCommand
from core.models import Developer

class Command(BaseCommand):
    help = 'Update developer counts with default values'

    def handle(self, *args, **options):
        # Set default values for all developers
        developers = Developer.objects.all()
        
        for dev in developers:
            # Set base values if they are zero or None
            if dev.project_count == 0 or dev.project_count is None:
                dev.project_count = 42
            if dev.follower_count == 0 or dev.follower_count is None:
                dev.follower_count = 58
            if dev.total_views == 0 or dev.total_views is None:
                dev.total_views = 120
            
            # Add actual approved projects count to base value
            actual_projects = dev.projects.filter(status='approved').count()
            if actual_projects > 0:
                dev.project_count = 42 + actual_projects
            
            dev.save()
            self.stdout.write(f"Updated {dev.full_name}: Projects={dev.project_count}, Followers={dev.follower_count}, Views={dev.total_views}")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {developers.count()} developers"))