# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User, Developer, Recruiter, Project


class DeveloperRegistrationForm(forms.Form):
    """Developer Registration Form"""
    full_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe'
        })
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered!')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match!')
        
        return cleaned_data
    
    def save(self):
        # Create User account (without full_name)
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            role='developer'
        )
        
        # Create Developer profile with full_name
        developer = Developer.objects.create(
            user=user,
            full_name=self.cleaned_data['full_name']
        )
        
        return user


class RecruiterRegistrationForm(forms.Form):
    """Recruiter Registration Form"""
    
    # Basic Information
    full_name = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe'
        })
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com'
        })
    )
    mobile_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 9876543210'
        })
    )
    job_title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'HR Manager'
        })
    )
    company_industry = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'IT Services'
        })
    )
    company_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VTS Solutions'
        })
    )
    company_website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com'
        })
    )
    business_proof = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control'
        })
    )
    company_location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Chennai'
        })
    )
    company_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe your company...',
            'rows': 3
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create password'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    verification_auth = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter verification code'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered!')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match!')
        
        if password and len(password) < 6:
            raise forms.ValidationError('Password must be at least 6 characters!')
        
        return cleaned_data
    
    def save(self):
        # Create User account
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            role='recruiter'
        )
        
        # Create Recruiter profile
        recruiter = Recruiter.objects.create(
            user=user,
            full_name=self.cleaned_data['full_name'],
            phone_number=self.cleaned_data.get('mobile_number', ''),
            hirer_job_title=self.cleaned_data.get('job_title', ''),
            company_name=self.cleaned_data.get('company_name', ''),
            company_industry=self.cleaned_data.get('company_industry', ''),
            company_website=self.cleaned_data.get('company_website', ''),
            company_location=self.cleaned_data.get('company_location', ''),
            company_description=self.cleaned_data.get('company_description', ''),
            verification_code=self.cleaned_data.get('verification_auth', ''),
            business_proof=self.cleaned_data.get('business_proof')
        )
        
        return user


class UserLoginForm(forms.Form):
    """Login form with email and password"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False, 
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                self.user_cache = authenticate(username=user.username, password=password)
                if self.user_cache is None:
                    raise forms.ValidationError('Invalid email or password')
                elif not self.user_cache.is_active:
                    raise forms.ValidationError('This account is inactive.')
            except User.DoesNotExist:
                raise forms.ValidationError('No account found with this email')
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class DeveloperProfileForm(forms.ModelForm):
    class Meta:
        model = Developer
        fields = [
            'full_name', 'title', 'bio', 'location', 'user_type', 'experience_level',
            'phone_number', 'github_url', 'twitter_url', 'linkedin_url', 'portfolio_url',
            'skills', 'hourly_rate', 'currency', 'profile_picture',
            'architecture_desc', 'modern_web_desc', 'performance_desc'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your full name',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Senior Full-Stack Developer'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Tell us about yourself, your experience, and what you specialize in...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Remote, New York, USA'
            }),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+1234567890'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://github.com/username'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://twitter.com/username'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://yourportfolio.com'
            }),
            'skills': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Python, Django, React, PostgreSQL, Docker'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '50',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('USD', 'USD ($)'),
                ('EUR', 'EUR (€)'),
                ('GBP', 'GBP (£)'),
                ('INR', 'INR (₹)')
            ]),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'onchange': 'previewImage(this)'
            }),
            'architecture_desc': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Scalable distributed systems and microservices'
            }),
            'modern_web_desc': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Next.js, React Server Components, edge computing'
            }),
            'performance_desc': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Core Web Vitals and optimized bundle sizes'
            }),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'summary', 'description', 'category', 'visibility',
            'cover_image', 'screenshots', 'video_url', 'video_start_time',
            'alt_text', 'caption', 'global_metadata', 'github_url', 'demo_url',
            'tech_stack', 'readme_content', 'default_branch', 'deployment_status',
            'license_type', 'contributors', 'system_requirements', 'api_docs_url',
            'url_slug', 'seo_keywords', 'meta_description', 'schedule_publish_date',
            'feature_in_hiring'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'screenshots': forms.HiddenInput(),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'video_start_time': forms.TextInput(attrs={'class': 'form-control'}),
            'alt_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'caption': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'global_metadata': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'demo_url': forms.URLInput(attrs={'class': 'form-control'}),
            'tech_stack': forms.HiddenInput(),
            'readme_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'default_branch': forms.TextInput(attrs={'class': 'form-control'}),
            'deployment_status': forms.TextInput(attrs={'class': 'form-control'}),
            'license_type': forms.Select(attrs={'class': 'form-select'}),
            'contributors': forms.TextInput(attrs={'class': 'form-control'}),
            'system_requirements': forms.TextInput(attrs={'class': 'form-control'}),
            'api_docs_url': forms.URLInput(attrs={'class': 'form-control'}),
            'url_slug': forms.TextInput(attrs={'class': 'form-control'}),
            'seo_keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'schedule_publish_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'feature_in_hiring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }