# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """Base User Model for authentication only"""
    
    ROLE_CHOICES = [
        ('admin','admin'),
        ('developer', 'Developer'),
        ('recruiter', 'Recruiter'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    email = models.EmailField(unique=True)
    
    # Common fields for both
    is_verified = models.BooleanField(default=False)
    joined_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    class Meta:
        db_table = 'users'
        ordering = ['-joined_date']



# core/models.py - Add profile_picture field

class Developer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='developer_profile')
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    
    # Add profile picture field
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Add these new fields to match your template
    title = models.CharField(max_length=200, blank=True, null=True, default='Developer')
    location = models.CharField(max_length=200, blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD', blank=True, null=True)
    
    experience_level = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('entry', 'Entry Level (0-2 years)'),
        ('junior', 'Junior (2-4 years)'),
        ('mid', 'Mid Level (4-7 years)'),
        ('senior', 'Senior (7-10 years)'),
        ('expert', 'Expert (10+ years)'),
    ])
    
    user_type = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('freelancer', 'Freelancer'),
        ('agency', 'Agency'),
        ('company', 'Company'),
    ])
    
    project_count = models.IntegerField(default=42)
    follower_count = models.IntegerField(default=620)
    total_views = models.IntegerField(default=349)
    
    architecture_desc = models.CharField(max_length=200, blank=True, null=True)
    modern_web_desc = models.CharField(max_length=200, blank=True, null=True)
    performance_desc = models.CharField(max_length=200, blank=True, null=True)
    
    profile_completed = models.BooleanField(default=False)
    
    verification_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_skills_list(self):
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
        return []
    
    # In core/models.py, update the Developer model:

def get_profile_picture_url(self):
    if self.profile_picture and hasattr(self.profile_picture, 'url') and self.profile_picture:
        return self.profile_picture.url
    return None  # Return None instead of a URL
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        db_table = 'developers'
        ordering = ['-created_at']
    


class Recruiter(models.Model):
    """Recruiter table - stores only recruiter data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    hirer_job_title = models.CharField(max_length=200, blank=True, null=True)
    
    # Company Information
    company_name = models.CharField(max_length=200, blank=True, null=True)
    company_industry = models.CharField(max_length=100, blank=True, null=True)
    company_website = models.URLField(blank=True, null=True)
    company_email = models.EmailField(blank=True, null=True)
    company_location = models.CharField(max_length=200, blank=True, null=True)
    company_size = models.CharField(max_length=50, blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)
    
    # Hiring Information
    hiring_role_type = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('in_house', 'In-house Recruiter'),
        ('agency', 'Recruitment Agency'),
        ('freelance', 'Freelance Recruiter'),
        ('hr_consultant', 'HR Consultant'),
        ('talent_acquisition', 'Talent Acquisition Specialist'),
    ])
    linkedin_profile_url = models.URLField(blank=True, null=True)
    
    # Verification
    verification_code = models.CharField(max_length=10, blank=True, null=True)
    business_proof = models.FileField(upload_to='business_proofs/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        db_table = 'recruiters'
        ordering = ['-created_at']

class Project(models.Model):
    CATEGORY_CHOICES = [
        ('web', 'Web Application'),
        ('mobile', 'Mobile App'),
        ('ai', 'AI & ML'),
        ('backend', 'Backend'),
        ('system', 'System Tool'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('draft', 'Draft Only'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'USD ($)'),
        ('EUR', 'EUR (€)'),
        ('GBP', 'GBP (£)'),
        ('INR', 'INR (₹)'),
        ('CAD', 'CAD ($)'),
        ('AUD', 'AUD ($)'),
    ]
    
    PRICE_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Rate'),
        ('negotiable', 'Negotiable'),
        ('free', 'Free'),
    ]
    
    # Basic Information
    developer = models.ForeignKey(Developer, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=500)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='web')
    
    # Pricing / Rate
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price/rate for the project")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    price_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES, default='fixed')
    
    # Visuals
    cover_image = models.ImageField(upload_to='project_covers/', null=True, blank=True)
    screenshots = models.JSONField(default=list, blank=True)
    video_url = models.URLField(blank=True, null=True)
    video_start_time = models.CharField(max_length=10, blank=True, null=True)
    
    # Accessibility
    alt_text = models.TextField(blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    global_metadata = models.BooleanField(default=True)
    
    # Technical Details
    github_url = models.URLField(blank=True, null=True)
    demo_url = models.URLField(blank=True, null=True)
    tech_stack = models.JSONField(default=list, blank=True)
    readme_content = models.TextField(blank=True, null=True)
    default_branch = models.CharField(max_length=100, default='main')
    deployment_status = models.CharField(max_length=100, blank=True, null=True)
    
    # Project Governance
    license_type = models.CharField(max_length=50, blank=True, null=True)
    contributors = models.CharField(max_length=500, blank=True, null=True)
    system_requirements = models.CharField(max_length=500, blank=True, null=True)
    api_docs_url = models.URLField(blank=True, null=True)
    
    # Discoverability
    url_slug = models.CharField(max_length=200, unique=True, blank=True, null=True)
    seo_keywords = models.CharField(max_length=500, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    
    # Visibility (No status field - projects are visible immediately)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    schedule_publish_date = models.DateTimeField(blank=True, null=True)
    feature_in_hiring = models.BooleanField(default=False)
    
    # Stats
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    def get_tech_stack_list(self):
        if self.tech_stack:
            return self.tech_stack if isinstance(self.tech_stack, list) else json.loads(self.tech_stack)
        return []
    
    def get_screenshots_list(self):
        if self.screenshots:
            return self.screenshots if isinstance(self.screenshots, list) else json.loads(self.screenshots)
        return []
    
    def get_formatted_price(self):
        """Return formatted price with currency symbol"""
        if not self.price:
            return "Negotiable"
        
        if self.price_type == 'free':
            return "Free"
        
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'INR': '₹',
            'CAD': 'C$',
            'AUD': 'A$',
        }
        symbol = symbols.get(self.currency, '$')
        
        if self.price_type == 'hourly':
            return f"{symbol}{self.price}/hr"
        else:
            return f"{symbol}{self.price}"
    
    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']

# In core/models.py, add this method to the Project class:
def get_formatted_price(self):
    """Return formatted price with currency symbol"""
    if not self.price:
        return "Negotiable"
    
    if self.price_type == 'free':
        return "Free"
    
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'INR': '₹',
        'CAD': 'C$',
        'AUD': 'A$',
    }
    symbol = symbols.get(self.currency, '$')
    
    if self.price_type == 'hourly':
        return f"{symbol}{self.price}/hr"
    else:
        return f"{symbol}{self.price}"

# Add this to your Project model in models.py if not already there
def get_formatted_price(self):
    """Return formatted price with currency symbol"""
    if not self.price:
        return "Negotiable"
    
    if self.price_type == 'free':
        return "Free"
    
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'INR': '₹',
        'CAD': 'C$',
        'AUD': 'A$',
    }
    symbol = symbols.get(self.currency, '$')
    
    if self.price_type == 'hourly':
        return f"{symbol}{self.price}/hr"
    else:
        return f"{symbol}{self.price}"

# Add these models to your core/models.py file

# Add these at the end of core/models.py

class Conversation(models.Model):
    """Represents a unique conversation between two users"""
    participant1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_participant1')
    participant2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_participant2')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        unique_together = ['participant1', 'participant2']
        ordering = ['-updated_at']
    
    def get_other_participant(self, current_user):
        if current_user == self.participant1:
            return self.participant2
        return self.participant1
    
    def get_last_message(self):
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    def __str__(self):
        return f"Conversation between {self.participant1.email} and {self.participant2.email}"


class Message(models.Model):
    """Represents a single message in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.email} to {self.receiver.email}"