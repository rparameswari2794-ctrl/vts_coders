# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import timedelta
import json
import base64
import re
import uuid
from django.db.models import Q, Max, OuterRef, Subquery
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import DeveloperRegistrationForm, RecruiterRegistrationForm, DeveloperProfileForm
from .models import User, Developer, Recruiter, Project, Conversation, Message, User


def common_home(request):
    """Common home page - shown to all visitors"""
    return render(request, 'core/home.html')


def login_view(request):
    """Login page - redirects to respective dashboard based on role after login"""
    if request.user.is_authenticated:
        if request.user.role == 'developer':
            return redirect('core:developer_home')
        elif request.user.role == 'recruiter':
            return redirect('core:recruiter_home')
        return redirect('core:home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'core/login.html')

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'core/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)

            messages.success(request, f'Welcome back {user.email}!')
            
            if user.role == 'developer':
                return redirect('core:developer_home')
            elif user.role == 'recruiter':
                return redirect('core:recruiter_home')
            else:
                return redirect('core:home')
        else:
            messages.error(request, 'Invalid password. Please try again.')

    return render(request, 'core/login.html')


def logout_view(request):
    """Logout user and redirect to common home page"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('core:home')


def developer_signup(request):
    """Developer signup page"""
    if request.user.is_authenticated:
        if request.user.role == 'developer':
            return redirect('core:developer_home')
        elif request.user.role == 'recruiter':
            return redirect('core:recruiter_home')
    
    if request.method == 'POST':
        form = DeveloperRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Account created successfully! Welcome to VTS Coders.')
                return redirect('core:developer_home')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = DeveloperRegistrationForm()
    
    return render(request, 'core/developer_signup.html', {'form': form})


def recruiter_signup(request):
    """Recruiter signup page"""
    if request.user.is_authenticated:
        if request.user.role == 'developer':
            return redirect('core:developer_home')
        elif request.user.role == 'recruiter':
            return redirect('core:recruiter_home')

    if request.method == 'POST':
        print("=" * 50)
        print("RECRUITER SIGNUP - POST DATA:")
        for key, value in request.POST.items():
            print(f"  {key}: {value}")
        print("=" * 50)
        
        form = RecruiterRegistrationForm(request.POST, request.FILES)
        print(f"Form is valid: {form.is_valid()}")
        
        if form.is_valid():
            try:
                user = form.save()
                print(f"User created: {user.email}, Role: {user.role}")
                
                login(request, user)
                print("User logged in successfully")
                
                messages.success(request, 'Account created successfully! Welcome to VTS Coders.')
                return redirect('core:recruiter_home')
            except Exception as e:
                print(f"ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            print("FORM ERRORS:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RecruiterRegistrationForm()

    return render(request, 'core/recruiter_signup.html', {'form': form})


# Developer Views (Protected)
@login_required
def developer_home(request):
    """Developer dashboard - only accessible to developers"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. This area is for developers only.')
        return redirect('core:home')
    
    try:
        developer = request.user.developer_profile
        # Remove status filter - just get all projects
        recent_projects = developer.projects.all().order_by('-created_at')[:3]
    except:
        recent_projects = []
    
    return render(request, 'developer/home.html', {
        'user': request.user,
        'recent_projects': recent_projects
    })


@login_required
def my_projects(request):
    """Developer projects page - shows all projects"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    try:
        developer = request.user.developer_profile
        all_projects = developer.projects.all().order_by('-created_at')
        # No status filters since status field is removed
        approved_projects = all_projects
        pending_projects = []
        rejected_projects = []
        draft_projects = developer.projects.filter(visibility='draft')
    except:
        all_projects = []
        approved_projects = []
        pending_projects = []
        rejected_projects = []
        draft_projects = []
    
    return render(request, 'developer/my_projects.html', {
        'user': request.user,
        'all_projects': all_projects,
        'approved_projects': approved_projects,
        'pending_projects': pending_projects,
        'rejected_projects': rejected_projects,
        'draft_projects': draft_projects,
    })


@login_required
def developer_profile(request):
    """View to display developer profile with projects"""
    
    try:
        developer = request.user.developer_profile
        
        if not developer.profile_completed:
            messages.info(request, 'Please complete your profile first.')
            return redirect('core:developer_profile_form')
        
        # Get all projects for the developer (recent first)
        recent_projects = developer.projects.all().order_by('-created_at')[:6]
        
        print(f"Found {recent_projects.count()} projects for {developer.full_name}")
        for p in recent_projects:
            print(f"  - {p.title} (Created: {p.created_at})")
        
        # Update total views
        if request.user != developer.user:
            developer.total_views += 1
            developer.save()
        
        context = {
            'developer': developer,
            'user': request.user,
            'projects': recent_projects,
        }
        return render(request, 'developer/profile.html', context)
        
    except Developer.DoesNotExist:
        messages.info(request, 'Please complete your profile first.')
        return redirect('core:developer_profile_form')
        
@login_required
def developer_profile_form(request):
    """View for developers to complete their profile"""
    
    # Check if user is a developer
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. This page is for developers only.')
        return redirect('core:home')
    
    # Get or create developer profile
    try:
        developer = request.user.developer_profile
        # If profile is already completed, redirect to profile view
        if developer.profile_completed:
            return redirect('core:developer_profile')
    except Developer.DoesNotExist:
        developer = None
    
    if request.method == 'POST':
        if developer:
            form = DeveloperProfileForm(request.POST, request.FILES, instance=developer)
        else:
            form = DeveloperProfileForm(request.POST, request.FILES)
        
        if form.is_valid():
            developer_profile = form.save(commit=False)
            developer_profile.user = request.user
            developer_profile.profile_completed = True
            developer_profile.save()
            
            messages.success(request, 'Your profile has been successfully created!')
            return redirect('core:developer_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        if developer:
            form = DeveloperProfileForm(instance=developer)
        else:
            form = DeveloperProfileForm()
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'developer/profile_form.html', context)




@login_required
def my_jobs(request):
    """Recruiter jobs page"""
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    return render(request, 'recruiter/my_jobs.html')


@login_required
def recruiter_profile(request):
    """Recruiter profile page"""
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    return render(request, 'recruiter/profile.html')


def chat_page(request):
    """Chat page - accessible to all logged-in users"""
    if not request.user.is_authenticated:
        return redirect('core:login')
    return render(request, 'core/chat.html')


# Explore & Public Pages
def explore_page(request):
    # Add index to each project for identification
    projects = [
    {'id': 1, 'title': 'NexFlow AI', 'author': 'Alex Rivers', 'category': 'ai', 'tags': ['Rust', 'Typescript', 'Wasm'], 'image': '/static/core/Image12.png', 'stars': 150, 'created_at': '2024-01-15', 'slug': 'nexflow-ai'},
    {'id': 2, 'title': 'AI-Powered Task Orchestrator', 'author': 'Jordan Smith', 'category': 'ai', 'tags': ['React', 'Python', 'OpenAI'], 'image': '/static/core/Image6.png', 'stars': 120, 'created_at': '2024-01-10', 'slug': 'ai-task-orchestrator'},
    {'id': 3, 'title': 'Real-Time Financial Dashboard', 'author': 'Marcus Vance', 'category': 'web', 'tags': ['D3.js', 'Node.js', 'Redis'], 'image': '/static/core/Image8a.png', 'stars': 200, 'created_at': '2024-01-05', 'slug': 'financial-dashboard'},
    {'id': 4, 'title': 'Minimalist E-Commerce', 'author': 'Elena Rossi', 'category': 'web', 'tags': ['Vue', 'Shopify API', 'SASS'], 'image': '/static/core/Image9.png', 'stars': 95, 'created_at': '2024-01-20', 'slug': 'minimalist-ecommerce'},
    {'id': 5, 'title': 'DevOps Monitoring CLI Tool', 'author': 'Marcus Miller', 'category': 'system', 'tags': ['GO', 'Docker', 'Rust'], 'image': '/static/core/Image10.png', 'stars': 180, 'created_at': '2024-01-08', 'slug': 'devops-monitor'},
    {'id': 6, 'title': 'Social Graph Visualization', 'author': 'Sofia Kumar', 'category': 'mobile', 'tags': ['Three.js', 'GraphQL', 'Neo4j'], 'image': '/static/core/Image11.png', 'stars': 110, 'created_at': '2024-01-12', 'slug': 'social-graph-viz'},
]    
    featured_devs = [
        {'name': 'Sarah Drasner', 'role': 'Sr. Frontend Eng', 'img': '/static/core/emily.png'},
        {'name': 'Guillermo Rauch', 'role': 'Vercel CEO', 'img': '/static/core/rauch.png'},
        {'name': 'Cassidy Williams', 'role': 'DX Engineer', 'img': '/static/core/jessica.png'},
        {'name': 'Marcus Miller', 'role': 'DevOps Expert', 'img': '/static/core/kent.png'},
    ]
    return render(request, 'core/explore.html', {
        'projects': projects,
        'featured_devs': featured_devs,
        'user': request.user,
    })

def developers_page(request):
    """Developers page - shows list of developers"""
    featured_devs = [
        {'name': 'Sarah Drasner', 'role': 'Sr. Frontend Eng', 'img': '/static/core/emily.png'},
        {'name': 'Guillermo Rauch', 'role': 'Vercel CEO', 'img': '/static/core/rauch.png'},
        {'name': 'Cassidy Williams', 'role': 'DX Engineer', 'img': '/static/core/jessica.png'},
        {'name': 'Marcus Miller', 'role': 'DevOps Expert', 'img': '/static/core/kent.png'},
    ]
    return render(request, 'core/developers.html', {
        'featured_devs': featured_devs,
        'user': request.user,
    })


def job_listings_page(request):
    """Job Listings page - shows available jobs"""
    return render(request, 'core/joblisting.html', {
        'user': request.user,
    })


@login_required
def recruiter_list(request):
    """Admin view to see all registered recruiters"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Only administrators can view this page.')
        return redirect('core:home')
    
    recruiters = User.objects.filter(role='recruiter').order_by('-joined_date')
    
    return render(request, 'core/recruiter_list.html', {
        'recruiters': recruiters,
        'total_recruiters': recruiters.count(),
    })


@login_required
def developer_explore_page(request):
    """Developer-specific explore page - shows projects for developers"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. This area is for developers only.')
        return redirect('core:home')
    
    projects = [
        {'id': 1, 'title': 'NexFlow AI', 'author': 'Alex Rivers', 'category': 'ai', 'tags': ['Rust', 'Typescript', 'Wasm'], 'image': '/static/core/Image12.png', 'stars': 150, 'created_at': '2024-01-15', 'slug': 'nexflow-ai'},
        {'id': 2, 'title': 'AI-Powered Task Orchestrator', 'author': 'Jordan Smith', 'category': 'ai', 'tags': ['React', 'Python', 'OpenAI'], 'image': '/static/core/Image6.png', 'stars': 120, 'created_at': '2024-01-10', 'slug': 'ai-task-orchestrator'},
        {'id': 3, 'title': 'Real-Time Financial Dashboard', 'author': 'Marcus Vance', 'category': 'web', 'tags': ['D3.js', 'Node.js', 'Redis'], 'image': '/static/core/Image8a.png', 'stars': 200, 'created_at': '2024-01-05', 'slug': 'financial-dashboard'},
        {'id': 4, 'title': 'Minimalist E-Commerce', 'author': 'Elena Rossi', 'category': 'web', 'tags': ['Vue', 'Shopify API', 'SASS'], 'image': '/static/core/Image9.png', 'stars': 95, 'created_at': '2024-01-20', 'slug': 'minimalist-ecommerce'},
        {'id': 5, 'title': 'DevOps Monitoring CLI Tool', 'author': 'Marcus Miller', 'category': 'system', 'tags': ['GO', 'Docker', 'Rust'], 'image': '/static/core/Image10.png', 'stars': 180, 'created_at': '2024-01-08', 'slug': 'devops-monitor'},
        {'id': 6, 'title': 'Social Graph Visualization', 'author': 'Sofia Kumar', 'category': 'mobile', 'tags': ['Three.js', 'GraphQL', 'Neo4j'], 'image': '/static/core/Image11.png', 'stars': 110, 'created_at': '2024-01-12', 'slug': 'social-graph-viz'},
    ]
    
    featured_devs = [
        {'name': 'Sarah Drasner', 'role': 'Sr. Frontend Eng', 'img': '/static/core/emily.png'},
        {'name': 'Guillermo Rauch', 'role': 'Vercel CEO', 'img': '/static/core/rauch.png'},
        {'name': 'Cassidy Williams', 'role': 'DX Engineer', 'img': '/static/core/jessica.png'},
        {'name': 'Marcus Miller', 'role': 'DevOps Expert', 'img': '/static/core/kent.png'},
    ]
    
    return render(request, 'developer/explore.html', {
        'projects': projects,
        'user': request.user,
        'featured_devs': featured_devs,
    })

@login_required
def developer_developers_page(request):
    """Developer-specific developers page - shows other developers"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. This area is for developers only.')
        return redirect('core:home')
    
    # Get all developers except the current user
    developers = User.objects.filter(role='developer').exclude(id=request.user.id)
    
    featured_devs = [
        {'name': 'Sarah Drasner', 'role': 'Sr. Frontend Eng', 'img': '/static/core/emily.png'},
        {'name': 'Guillermo Rauch', 'role': 'Vercel CEO', 'img': '/static/core/rauch.png'},
        {'name': 'Cassidy Williams', 'role': 'DX Engineer', 'img': '/static/core/jessica.png'},
        {'name': 'Marcus Miller', 'role': 'DevOps Expert', 'img': '/static/core/kent.png'},
    ]
    
    return render(request, 'developer/developers.html', {
        'developers': developers,
        'featured_devs': featured_devs,
        'user': request.user,
    })


# Project Upload Views
@login_required
def upload_project(request):
    """Upload project page - for developers to upload their projects"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. Only developers can upload projects.')
        return redirect('core:home')
    
    return render(request, 'developer/upload_project.html', {
        'user': request.user,
    })


@login_required
def upload_project_step1(request):
    """Upload project step 1 - Basic Information"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. Only developers can upload projects.')
        return redirect('core:developer_home')
    
    # Get developer profile
    try:
        developer = request.user.developer_profile
        full_name = developer.full_name if developer and developer.full_name else request.user.email
        designation = developer.title if developer and developer.title else 'Developer'
    except Developer.DoesNotExist:
        developer = None
        full_name = request.user.email
        designation = 'Developer'
    
    if request.method == 'POST':
        # Get data from POST
        project_title = request.POST.get('title', '')
        project_summary = request.POST.get('summary', '')
        project_description = request.POST.get('description', '')
        project_category = request.POST.get('category', 'web')
        project_visibility = request.POST.get('visibility', 'public')
        
        # Save to session
        request.session['project_title'] = project_title
        request.session['project_summary'] = project_summary
        request.session['project_description'] = project_description
        request.session['project_category'] = project_category
        request.session['project_visibility'] = project_visibility
        request.session.modified = True
        
        return redirect('core:upload_project_step2')
    
    context = {
        'user': request.user,
        'developer': developer,
        'full_name': full_name,
        'designation': designation,
    }
    return render(request, 'developer/upload_project_step1.html', context)


@login_required
def upload_project_step2(request):
    """Upload project step 2 - Visuals"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. Only developers can upload projects.')
        return redirect('core:developer_home')
    
    # Get developer profile
    try:
        developer = request.user.developer_profile
        
        # Check if profile is completed
        if not developer.profile_completed:
            messages.warning(request, 'Please complete your profile first before uploading a project.')
            return redirect('core:developer_profile_form')
        
        full_name = developer.full_name if developer.full_name else request.user.email
        designation = developer.title if developer.title else 'Developer'
        profile_picture = developer.profile_picture.url if developer.profile_picture else None
        
        print("=" * 50)
        print(f"Developer: {developer}")
        print(f"Full Name: {full_name}")
        print(f"Designation: {designation}")
        print(f"Profile Completed: {developer.profile_completed}")
        print("=" * 50)
        
    except Developer.DoesNotExist:
        messages.warning(request, 'Please complete your profile first before uploading a project.')
        return redirect('core:developer_profile_form')
    
    context = {
        'user': request.user,
        'developer': developer,
        'full_name': full_name,
        'designation': designation,
        'profile_picture': profile_picture,
        'project_title': request.session.get('project_title', ''),
        'project_summary': request.session.get('project_summary', ''),
        'project_description': request.session.get('project_description', ''),
        'project_category': request.session.get('project_category', 'web'),
        'project_visibility': request.session.get('project_visibility', 'public'),
    }
    
    return render(request, 'developer/upload_project_step2.html', context)

@login_required
def upload_project_step3(request):
    """Upload project step 3 - Technical Details"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. Only developers can upload projects.')
        return redirect('core:developer_home')
    
    # Get developer profile
    try:
        developer = request.user.developer_profile
        full_name = developer.full_name if developer and developer.full_name else request.user.email
        designation = developer.title if developer and developer.title else 'Developer'
    except Developer.DoesNotExist:
        developer = None
        full_name = request.user.email
        designation = 'Developer'
    
    if request.method == 'POST':
        # Save technical data to session
        request.session['github_url'] = request.POST.get('github_url', '')
        request.session['demo_url'] = request.POST.get('demo_url', '')
        request.session['tech_stack'] = request.POST.get('tech_stack', '[]')
        request.session['readme_content'] = request.POST.get('readme_content', '')
        request.session['license_type'] = request.POST.get('license_type', 'MIT')
        request.session.modified = True
        return redirect('core:upload_project_step4')
    
    context = {
        'user': request.user,
        'developer': developer,
        'full_name': full_name,
        'designation': designation,
        'project_title': request.session.get('project_title', ''),
        'project_summary': request.session.get('project_summary', ''),
        'project_description': request.session.get('project_description', ''),
        'project_category': request.session.get('project_category', ''),
        'project_visibility': request.session.get('project_visibility', 'public'),
        'github_url': request.session.get('github_url', ''),
        'demo_url': request.session.get('demo_url', ''),
        'tech_stack': request.session.get('tech_stack', '[]'),
        'readme_content': request.session.get('readme_content', ''),
        'license_type': request.session.get('license_type', 'MIT'),
    }
    
    return render(request, 'developer/upload_project_step3.html', context)


@login_required
def upload_project_step4(request):
    """Upload project step 4 - Publish"""
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. Only developers can upload projects.')
        return redirect('core:developer_home')
    
    # Get developer profile
    try:
        developer = request.user.developer_profile
        full_name = developer.full_name if developer and developer.full_name else request.user.email
        designation = developer.title if developer and developer.title else 'Developer'
        profile_picture = developer.profile_picture.url if developer and developer.profile_picture else None
    except Developer.DoesNotExist:
        developer = None
        full_name = request.user.email
        designation = 'Developer'
        profile_picture = None
    
    context = {
        'user': request.user,
        'developer': developer,
        'full_name': full_name,
        'designation': designation,
        'profile_picture': profile_picture,
        'project_title': request.session.get('project_title', ''),
        'project_summary': request.session.get('project_summary', ''),
        'project_description': request.session.get('project_description', ''),
        'project_category': request.session.get('project_category', ''),
        'project_visibility': request.session.get('project_visibility', 'public'),
        'github_url': request.session.get('github_url', ''),
        'demo_url': request.session.get('demo_url', ''),
        'tech_stack': request.session.get('tech_stack', '[]'),
        'readme_content': request.session.get('readme_content', ''),
        'license_type': request.session.get('license_type', 'MIT'),
    }
    
    return render(request, 'developer/upload_project_step4.html', context)


@login_required
def save_project(request):
    """Save project to database - called via AJAX from step 4"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Get developer profile
        try:
            developer = request.user.developer_profile
        except Developer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Developer profile not found'}, status=400)
        
        print("=" * 50)
        print(f"Saving project for: {developer.full_name}")
        print(f"Project data: {data}")
        print("=" * 50)
        
        # Get basic project info
        title = data.get('title', '')
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)
        
        summary = data.get('summary', '')
        description = data.get('description', '')
        category = data.get('category', 'web')
        visibility = data.get('visibility', 'public')
        
        # Generate slug
        url_slug = generate_slug(title)
        original_slug = url_slug
        counter = 1
        while Project.objects.filter(url_slug=url_slug).exists():
            url_slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Handle cover image from base64
        cover_image = None
        cover_image_data = data.get('coverImage')
        if cover_image_data and cover_image_data != 'present' and cover_image_data != 'null' and cover_image_data != 'None':
            if ',' in cover_image_data:
                format, imgstr = cover_image_data.split(';base64,')
                ext = format.split('/')[-1] if '/' in format else 'png'
                cover_image = ContentFile(base64.b64decode(imgstr), name=f'cover_{uuid.uuid4().hex}.{ext}')
        
        # Parse tech stack
        tech_stack = data.get('techStack', [])
        if isinstance(tech_stack, str):
            try:
                tech_stack = json.loads(tech_stack)
            except:
                tech_stack = []
        
        # Create the project
        project = Project.objects.create(
            developer=developer,
            title=title,
            summary=summary,
            description=description,
            category=category,
            visibility=visibility,
            cover_image=cover_image,
            video_url=data.get('videoUrl', ''),
            video_start_time=data.get('videoStartTime', ''),
            alt_text=data.get('altText', ''),
            caption=data.get('caption', ''),
            global_metadata=data.get('globalMetadata', True),
            github_url=data.get('githubUrl', ''),
            demo_url=data.get('demoUrl', ''),
            tech_stack=tech_stack,
            readme_content=data.get('readmeContent', ''),
            license_type=data.get('licenseType', 'MIT'),
            url_slug=url_slug,
            seo_keywords=data.get('seoKeywords', ''),
            meta_description=data.get('metaDescription', ''),
            feature_in_hiring=data.get('hiringCheck', False),
            price=data.get('price', None),
            currency=data.get('currency', 'USD'),
            price_type=data.get('price_type', 'fixed'),
            published_at=timezone.now()
        )
        
        print(f"Project created: {project.title} (ID: {project.id})")
        
        # Update developer's project count
        developer.project_count = developer.projects.count()
        developer.save()
        
        print(f"Developer project count: {developer.project_count}")
        
        # Clear session data
        for key in ['project_title', 'project_summary', 'project_description', 'project_category', 
                    'project_visibility', 'github_url', 'demo_url', 'tech_stack', 'readme_content', 'license_type']:
            if key in request.session:
                del request.session[key]
        
        return JsonResponse({
            'success': True,
            'project_id': project.id,
            'message': 'Project published successfully!',
            'slug': url_slug
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def developer_projects_api(request):
    """API endpoint to get developer's projects"""
    try:
        developer = request.user.developer_profile
        # Remove status filter
        projects = developer.projects.all().order_by('-created_at')[:6]
        
        projects_data = []
        for project in projects:
            projects_data.append({
                'id': project.id,
                'title': project.title,
                'summary': project.summary,
                'category': project.category,
                'cover_image': project.cover_image.url if project.cover_image else None,
                'tech_stack': project.get_tech_stack_list(),
                'views_count': project.views_count,
                'likes_count': project.likes_count,
                'created_at': project.created_at.isoformat(),
                'url_slug': project.url_slug,
            })
        
        return JsonResponse({'success': True, 'projects': projects_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def project_preview(request):
    """Preview project before publishing"""
    return render(request, 'developer/project_preview.html')


def generate_slug(title):
    """Generate URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    if len(slug) > 100:
        slug = slug[:100]
    return slug

@login_required
def developer_profile_edit(request):
    """View for developers to edit their profile"""
    
    # Check if user is a developer
    if request.user.role != 'developer':
        messages.error(request, 'Access denied. This page is for developers only.')
        return redirect('core:home')
    
    try:
        developer = request.user.developer_profile
    except Developer.DoesNotExist:
        messages.info(request, 'Please complete your profile first.')
        return redirect('core:developer_profile_form')
    
    if request.method == 'POST':
        # Manually handle form data to avoid ClearableFileInput issues
        developer.full_name = request.POST.get('full_name', developer.full_name)
        developer.title = request.POST.get('title', developer.title)
        developer.bio = request.POST.get('bio', developer.bio)
        developer.location = request.POST.get('location', developer.location)
        developer.user_type = request.POST.get('user_type', developer.user_type)
        developer.experience_level = request.POST.get('experience_level', developer.experience_level)
        developer.phone_number = request.POST.get('phone_number', developer.phone_number)
        developer.github_url = request.POST.get('github_url', developer.github_url)
        developer.twitter_url = request.POST.get('twitter_url', developer.twitter_url)
        developer.linkedin_url = request.POST.get('linkedin_url', developer.linkedin_url)
        developer.portfolio_url = request.POST.get('portfolio_url', developer.portfolio_url)
        developer.skills = request.POST.get('skills', developer.skills)
        developer.hourly_rate = request.POST.get('hourly_rate', developer.hourly_rate)
        developer.currency = request.POST.get('currency', developer.currency)
        developer.architecture_desc = request.POST.get('architecture_desc', developer.architecture_desc)
        developer.modern_web_desc = request.POST.get('modern_web_desc', developer.modern_web_desc)
        developer.performance_desc = request.POST.get('performance_desc', developer.performance_desc)
        
        # Handle profile picture
        if request.FILES.get('profile_picture'):
            developer.profile_picture = request.FILES.get('profile_picture')
        
        # Handle picture removal
        if request.POST.get('profile_picture-clear') == 'on':
            if developer.profile_picture:
                developer.profile_picture.delete(save=False)
                developer.profile_picture = None
        
        developer.save()
        messages.success(request, 'Your profile has been successfully updated!')
        return redirect('core:developer_profile')
    
    context = {
        'developer': developer,
        'user': request.user,
    }
    return render(request, 'developer/profile_edit.html', context)

# Add these views after your existing recruiter views

@login_required
def recruiter_explore(request):
    """Recruiter explore page - shows projects and talent"""
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied. This area is for recruiters only.')
        return redirect('core:home')
    
    projects = [
        {'id': 1, 'title': 'NexFlow AI', 'author': 'Alex Rivers', 'category': 'ai', 'tags': ['Rust', 'Typescript', 'Wasm'], 'image': '/static/core/Image12.png', 'stars': 150, 'created_at': '2024-01-15', 'slug': 'nexflow-ai'},
        {'id': 2, 'title': 'AI-Powered Task Orchestrator', 'author': 'Jordan Smith', 'category': 'ai', 'tags': ['React', 'Python', 'OpenAI'], 'image': '/static/core/Image6.png', 'stars': 120, 'created_at': '2024-01-10', 'slug': 'ai-task-orchestrator'},
        {'id': 3, 'title': 'Real-Time Financial Dashboard', 'author': 'Marcus Vance', 'category': 'web', 'tags': ['D3.js', 'Node.js', 'Redis'], 'image': '/static/core/Image8a.png', 'stars': 200, 'created_at': '2024-01-05', 'slug': 'financial-dashboard'},
        {'id': 4, 'title': 'Minimalist E-Commerce', 'author': 'Elena Rossi', 'category': 'web', 'tags': ['Vue', 'Shopify API', 'SASS'], 'image': '/static/core/Image9.png', 'stars': 95, 'created_at': '2024-01-20', 'slug': 'minimalist-ecommerce'},
        {'id': 5, 'title': 'DevOps Monitoring CLI Tool', 'author': 'Marcus Miller', 'category': 'system', 'tags': ['GO', 'Docker', 'Rust'], 'image': '/static/core/Image10.png', 'stars': 180, 'created_at': '2024-01-08', 'slug': 'devops-monitor'},
        {'id': 6, 'title': 'Social Graph Visualization', 'author': 'Sofia Kumar', 'category': 'mobile', 'tags': ['Three.js', 'GraphQL', 'Neo4j'], 'image': '/static/core/Image11.png', 'stars': 110, 'created_at': '2024-01-12', 'slug': 'social-graph-viz'},
    ]
    
    return render(request, 'recruiter/explore.html', {
        'user': request.user,
        'projects': projects,
    })


@login_required
def recruiter_developers(request):
    """Recruiter developers page - shows developers list"""
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied. This area is for recruiters only.')
        return redirect('core:home')
    
    # Get all developers (users with role 'developer' who have completed profile)
    developers = Developer.objects.filter(profile_completed=True).select_related('user')
    
    return render(request, 'recruiter/developers.html', {
        'user': request.user,
        'developers': developers,
    })

# core/views.py - Fixed recruiter_home view

@login_required
def recruiter_home(request):
    """Recruiter home/dashboard page - Main landing page for recruiters"""
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied. This area is for recruiters only.')
        return redirect('core:home')
    
    try:
        recruiter = request.user.recruiter_profile
        print(f"Recruiter found: {recruiter}")
    except Recruiter.DoesNotExist:
        recruiter = None
        print("No recruiter profile found")
    
    # Get recent developers and projects
    try:
        recent_developers = Developer.objects.filter(profile_completed=True).order_by('-created_at')[:6]
        recent_projects = Project.objects.filter(visibility='public').order_by('-created_at')[:6]
        print(f"Found {recent_developers.count()} developers and {recent_projects.count()} projects")
    except Exception as e:
        print(f"Error fetching data: {e}")
        recent_developers = []
        recent_projects = []
    
    context = {
        'user': request.user,
        'recruiter': recruiter,
        'recent_developers': recent_developers,
        'recent_projects': recent_projects,
    }
    
    return render(request, 'recruiter/home.html', context)

@login_required
def recruiter_dashboard(request):
    """Recruiter Dashboard - separate from home page"""
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied. This area is for recruiters only.')
        return redirect('core:home')
    
    try:
        recruiter = request.user.recruiter_profile
    except Recruiter.DoesNotExist:
        recruiter = None
    
    # Get statistics
    total_jobs_posted = 0  # Replace with actual count from Job model
    active_applications = 0  # Replace with actual count
    total_views = recruiter.total_views if hasattr(recruiter, 'total_views') else 0
    
    # Get recent developers (newest)
    recent_developers = Developer.objects.filter(profile_completed=True).order_by('-created_at')[:5]
    
    # Get featured projects
    featured_projects = Project.objects.filter(visibility='public').order_by('-created_at')[:6]
    
    context = {
        'user': request.user,
        'recruiter': recruiter,
        'total_jobs_posted': total_jobs_posted,
        'active_applications': active_applications,
        'total_views': total_views,
        'recent_developers': recent_developers,
        'featured_projects': featured_projects,
    }
    return render(request, 'recruiter/dashboard.html', context)




# In your developers_list_api function
@login_required
def developers_list_api(request):
    """API endpoint to get all developers for recruiter dashboard"""
    
    if request.user.role != 'recruiter':
        return JsonResponse(
            {'success': False, 'error': 'Access denied'},
            status=403
        )

    try:
        developers = (
            Developer.objects
            .filter(profile_completed=True)
            .select_related('user')
            .order_by('-created_at')
        )

        one_week_ago = timezone.now() - timedelta(days=7)
        developers_data = []

        for dev in developers:
            is_new = dev.created_at >= one_week_ago
            
            # Role Detection
            role = 'fullstack'
            if dev.title:
                title_lower = dev.title.lower()
                if 'frontend' in title_lower or 'front-end' in title_lower or 'ui' in title_lower:
                    role = 'frontend'
                elif 'backend' in title_lower or 'back-end' in title_lower or 'api' in title_lower:
                    role = 'backend'
                elif 'designer' in title_lower or 'ui/ux' in title_lower:
                    role = 'designer'

            is_senior = dev.experience_level in ['senior', 'expert']
            is_remote = dev.location and 'remote' in dev.location.lower()
            
            skills_list = dev.get_skills_list() if hasattr(dev, 'get_skills_list') else []
            
            # FIX: Build the correct absolute URL for profile picture
            avatar_url = None
            if dev.profile_picture and dev.profile_picture.name:
                # This will return the full URL path
                avatar_url = dev.profile_picture.url
                print(f"Developer {dev.full_name} - Profile picture path: {dev.profile_picture.name}")
                print(f"Full URL: {avatar_url}")
            
            # If no profile picture, use fallback
            if not avatar_url:
                avatar_url = f"https://ui-avatars.com/api/?name={dev.full_name.replace(' ', '+')}&background=1e2a78&color=fff&size=100"

            developers_data.append({
                'id': dev.id,
                'full_name': dev.full_name,
                'title': dev.title or 'Developer',
                'bio': dev.bio or 'Passionate developer',
                'skills': dev.skills or '',
                'skills_list': skills_list,
                'location': dev.location or 'Remote',
                'experience': dev.get_experience_level_display(),
                'is_senior': is_senior,
                'is_remote': is_remote,
                'is_new': is_new,
                'role': role,
                'avatar': avatar_url,  # This will now be the correct URL
                'created_at': dev.created_at.isoformat(),
                'joined_date': dev.created_at.strftime('%b %d, %Y'),
                'profile_completed': dev.profile_completed,
            })

        return JsonResponse({
            'success': True,
            'developers': developers_data,
            'count': len(developers_data)
        })

    except Exception as e:
        print("Error:", str(e))
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def chat_page(request, user_id=None):
    """Chat page - accessible to all logged-in users"""
    if not request.user.is_authenticated:
        return redirect('core:login')
    return render(request, 'core/chat.html', {'user': request.user})


@login_required
def get_all_users(request):
    """Get all users (developers and recruiters) except current user and admin"""
    try:
        users = User.objects.exclude(id=request.user.id).exclude(role='admin')
        
        users_data = []
        for user in users:
            full_name = user.username
            title = ''
            avatar_url = None
            
            if user.role == 'developer':
                try:
                    dev = Developer.objects.get(user=user)
                    full_name = dev.full_name or user.get_full_name() or user.username
                    title = dev.title or 'Developer'
                    # Only set avatar_url if profile_picture exists
                    if dev.profile_picture and hasattr(dev.profile_picture, 'url'):
                        avatar_url = dev.profile_picture.url
                except Developer.DoesNotExist:
                    full_name = user.get_full_name() or user.username
                    title = 'Developer'
            elif user.role == 'recruiter':
                try:
                    rec = Recruiter.objects.get(user=user)
                    full_name = rec.full_name or user.get_full_name() or user.username
                    title = rec.hirer_job_title or 'Recruiter'
                    # Recruiters might not have profile_picture field, so skip
                except Recruiter.DoesNotExist:
                    full_name = user.get_full_name() or user.username
                    title = 'Recruiter'
            
            users_data.append({
                'id': user.id,
                'full_name': full_name,
                'role': user.role,
                'title': title,
                'avatar_url': avatar_url,  # Send None if no profile picture
            })
        
        return JsonResponse({'success': True, 'users': users_data})
    except Exception as e:
        print(f"Error in get_all_users: {str(e)}")
        return JsonResponse({'success': True, 'users': []})

@login_required
def get_developers_api(request):
    """API to get developers from database"""
    developers = Developer.objects.filter(profile_completed=True).select_related('user')
    
    developers_data = []
    for dev in developers:
        developers_data.append({
            'id': dev.id,
            'name': dev.full_name,
            'title': dev.title,
            'location': dev.location or 'Remote',
            'remote': 'remote' in dev.location.lower() if dev.location else False,
            'experience': dev.get_experience_years(),
            'experienceText': f"{dev.get_experience_years()} years",
            'match': 85,  # Calculate based on skills
            'skills': dev.get_skills_list(),
            'about': dev.bio,
            'salary': f"${dev.hourly_rate}/hr" if dev.hourly_rate else "Negotiable",
            'avatar': dev.profile_picture.url if dev.profile_picture else f"https://ui-avatars.com/api/?name={dev.full_name.replace(' ', '+')}&background=1a1f36&color=fff",
            'portfolio': dev.portfolio_url or '#',
        })
    
    return JsonResponse({'success': True, 'developers': developers_data})


@login_required
def get_conversations(request):
    """Get all conversations for the current user"""
    try:
        conversations = Conversation.objects.filter(
            Q(participant1=request.user) | Q(participant2=request.user)
        ).order_by('-updated_at')
        
        result = []
        for conv in conversations:
            other_user = conv.get_other_participant(request.user)
            
            if other_user.role == 'admin':
                continue
            
            full_name = other_user.username
            title = ''
            avatar_url = None
            
            if other_user.role == 'developer':
                try:
                    dev = Developer.objects.get(user=other_user)
                    full_name = dev.full_name or other_user.get_full_name() or other_user.username
                    title = dev.title or 'Developer'
                    if dev.profile_picture and hasattr(dev.profile_picture, 'url'):
                        avatar_url = dev.profile_picture.url
                except Developer.DoesNotExist:
                    full_name = other_user.get_full_name() or other_user.username
                    title = 'Developer'
            elif other_user.role == 'recruiter':
                try:
                    rec = Recruiter.objects.get(user=other_user)
                    full_name = rec.full_name or other_user.get_full_name() or other_user.username
                    title = rec.hirer_job_title or 'Recruiter'
                except Recruiter.DoesNotExist:
                    full_name = other_user.get_full_name() or other_user.username
                    title = 'Recruiter'
            
            last_msg = conv.get_last_message()
            
            result.append({
                'id': conv.id,
                'other_user': {
                    'id': other_user.id,
                    'full_name': full_name,
                    'role': other_user.role,
                    'title': title,
                    'avatar_url': avatar_url,
                },
                'last_message': {
                    'content': last_msg.content if last_msg else None,
                    'sender': last_msg.sender.id if last_msg else None,
                    'time': last_msg.created_at.strftime('%I:%M %p') if last_msg else None,
                } if last_msg else None,
                'unread_count': conv.get_unread_count(request.user),
            })
        
        return JsonResponse({'success': True, 'conversations': result})
    except Exception as e:
        print(f"Error in get_conversations: {str(e)}")
        return JsonResponse({'success': True, 'conversations': []})


@login_required
def get_messages(request, conversation_id):
    """Get all messages for a conversation"""
    try:
        conv = Conversation.objects.get(id=conversation_id)
        if request.user not in [conv.participant1, conv.participant2]:
            return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
        
        messages = conv.messages.all()
        result = []
        for msg in messages:
            result.append({
                'id': msg.id,
                'sender_id': msg.sender.id,
                'content': msg.content,
                'time': msg.created_at.strftime('%I:%M %p'),
                'date': msg.created_at.strftime('%B %d, %Y'),
            })
        
        return JsonResponse({'success': True, 'messages': result})
    except Conversation.DoesNotExist:
        return JsonResponse({'success': True, 'messages': []})
    except Exception as e:
        print(f"Error in get_messages: {str(e)}")
        return JsonResponse({'success': True, 'messages': []})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_message(request):
    """Send a new message"""
    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        
        content = data.get('content', '').strip()
        receiver_id = data.get('receiver_id')
        
        # Validate
        if not content:
            return JsonResponse({'success': False, 'error': 'Message content is required'}, status=400)
        
        if not receiver_id:
            return JsonResponse({'success': False, 'error': 'Receiver ID is required'}, status=400)
        
        # Get receiver
        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Receiver not found'}, status=404)
        
        # Get or create conversation using participant1 and participant2
        # Always order participants by ID to ensure uniqueness
        user1, user2 = sorted([request.user, receiver], key=lambda x: x.id)
        conversation, created = Conversation.objects.get_or_create(
            participant1=user1,
            participant2=user2
        )
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            receiver=receiver,
            content=content
        )
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'time': message.created_at.strftime('%I:%M %p'),
                'date': message.created_at.strftime('%B %d, %Y'),
            },
            'conversation_id': conversation.id
        })
        
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def mark_messages_read(request, conversation_id):
    """Mark all messages as read"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        if request.user not in [conversation.participant1, conversation.participant2]:
            return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
        
        other_user = conversation.get_other_participant(request.user)
        count = conversation.messages.filter(sender=other_user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return JsonResponse({'success': True, 'marked_count': count})
        
    except Conversation.DoesNotExist:
        return JsonResponse({'success': True, 'marked_count': 0})
    except Exception as e:
        print(f"Error in mark_messages_read: {str(e)}")
        return JsonResponse({'success': True, 'marked_count': 0})


@login_required
def recruiters_list_api(request):
    """API endpoint to get all recruiters (exclude admin)"""
    try:
        recruiters = Recruiter.objects.exclude(user__role='admin').select_related('user').order_by('-created_at')
        
        recruiters_data = []
        for rec in recruiters:
            recruiters_data.append({
                'id': rec.user.id,
                'full_name': rec.full_name,
                'hirer_job_title': rec.hirer_job_title or 'Recruiter',
                'role': 'recruiter',
                'avatar': '',
                'company_description': rec.company_description or 'Talent acquisition specialist',
            })
        
        return JsonResponse({'success': True, 'recruiters': recruiters_data})
    except Exception as e:
        print(f"Error in recruiters_list_api: {str(e)}")
        return JsonResponse({'success': True, 'recruiters': []})


def project_detail(request, slug):
    """View to display a single project detail - PUBLIC accessible"""
    
    # Print for debugging
    print(f"Looking for project with slug: {slug}")
    
    # Demo projects with matching slugs from your explore page
    demo_projects = {
        'nexflow-ai': {
            'title': 'NexFlow AI',
            'summary': 'Enterprise-grade artificial intelligence solution that transforms data workflows into intelligent automation.',
            'description': 'Modern enterprises struggle with fragmented data pipelines, manual processing bottlenecks, and lack of real-time intelligence. Traditional solutions require extensive engineering resources and fail to adapt to dynamic business needs.',
            'category': 'ai',
            'views_count': 1250,
            'likes_count': 89,
            'shares_count': 34,
            'created_at': '2024-01-15',
            'demo_url': '#',
            'github_url': '#',
            'tech_stack': ['Rust', 'TypeScript', 'Wasm', 'Python', 'TensorFlow', 'Kubernetes', 'FastAPI', 'PostgreSQL', 'Redis'],
            'visibility': 'public',
            'published_at': '2024-01-15',
            'developer': {
                'full_name': 'Alex Rivers',
                'title': 'Lead AI Engineer',
                'bio': 'Director of Machine Learning with 12+ years experience.',
                'profile_picture': None,
                'github_url': 'https://github.com/alexrivers',
                'portfolio_url': 'https://alexrivers.dev',
                'linkedin_url': 'https://linkedin.com/in/alexrivers',
                'skills': 'Python, TensorFlow, PyTorch, AWS, Docker',
                'user_id': 1
            }
        },
        'ai-task-orchestrator': {
            'title': 'AI-Powered Task Orchestrator',
            'summary': 'Intelligent task management system powered by advanced AI algorithms.',
            'description': 'A comprehensive task orchestration platform that uses AI to optimize workflow distribution.',
            'category': 'ai',
            'views_count': 890,
            'likes_count': 67,
            'shares_count': 23,
            'created_at': '2024-01-10',
            'demo_url': '#',
            'github_url': '#',
            'tech_stack': ['React', 'Python', 'OpenAI', 'Django', 'Celery', 'Redis'],
            'visibility': 'public',
            'developer': {
                'full_name': 'Jordan Smith',
                'title': 'AI Engineer',
                'bio': 'AI specialist with focus on workflow automation.',
                'profile_picture': None,
                'skills': 'Python, OpenAI, Django, Celery',
                'user_id': 2
            }
        },
        'financial-dashboard': {
            'title': 'Real-Time Financial Dashboard',
            'summary': 'Interactive dashboard for real-time financial data visualization.',
            'description': 'A powerful dashboard that displays financial metrics and analytics in real-time.',
            'category': 'web',
            'views_count': 2100,
            'likes_count': 156,
            'shares_count': 78,
            'created_at': '2024-01-05',
            'demo_url': '#',
            'github_url': '#',
            'tech_stack': ['D3.js', 'Node.js', 'Redis', 'WebSocket', 'Express', 'MongoDB'],
            'visibility': 'public',
            'developer': {
                'full_name': 'Marcus Vance',
                'title': 'Full Stack Developer',
                'bio': 'Full stack developer with expertise in data visualization.',
                'profile_picture': None,
                'skills': 'JavaScript, D3.js, Node.js, MongoDB',
                'user_id': 3
            }
        },
        'minimalist-ecommerce': {
            'title': 'Minimalist E-Commerce',
            'summary': 'Clean and modern e-commerce platform with great UX.',
            'description': 'A minimalist e-commerce solution focused on user experience and performance.',
            'category': 'web',
            'views_count': 567,
            'likes_count': 45,
            'shares_count': 12,
            'created_at': '2024-01-20',
            'demo_url': '#',
            'github_url': '#',
            'tech_stack': ['Vue', 'Shopify API', 'SASS', 'Node.js', 'MongoDB'],
            'visibility': 'public',
            'developer': {
                'full_name': 'Elena Rossi',
                'title': 'Frontend Developer',
                'bio': 'UI/UX focused frontend developer.',
                'profile_picture': None,
                'skills': 'Vue.js, SASS, Node.js',
                'user_id': 4
            }
        },
        'devops-monitor': {
            'title': 'DevOps Monitoring CLI Tool',
            'summary': 'Command-line tool for infrastructure monitoring.',
            'description': 'A powerful CLI tool for monitoring and managing DevOps infrastructure.',
            'category': 'system',
            'views_count': 432,
            'likes_count': 34,
            'shares_count': 9,
            'created_at': '2024-01-08',
            'demo_url': '#',
            'github_url': '#',
            'tech_stack': ['GO', 'Docker', 'Rust', 'Prometheus', 'Grafana'],
            'visibility': 'public',
            'developer': {
                'full_name': 'Marcus Miller',
                'title': 'DevOps Engineer',
                'bio': 'DevOps expert with focus on automation.',
                'profile_picture': None,
                'skills': 'Go, Docker, Kubernetes, Prometheus',
                'user_id': 5
            }
        },
        'social-graph-viz': {
            'title': 'Social Graph Visualization',
            'summary': 'Interactive social network visualization tool.',
            'description': 'A tool for visualizing and analyzing social network connections.',
            'category': 'mobile',
            'views_count': 678,
            'likes_count': 56,
            'shares_count': 21,
            'created_at': '2024-01-12',
            'demo_url': '#',
            'github_url': '#',
            'tech_stack': ['Three.js', 'GraphQL', 'Neo4j', 'React Native'],
            'visibility': 'public',
            'developer': {
                'full_name': 'Sofia Kumar',
                'title': 'Mobile Developer',
                'bio': 'Mobile development specialist.',
                'profile_picture': None,
                'skills': 'React Native, GraphQL, Neo4j',
                'user_id': 6
            }
        },
    }
    
    # Check if it's a demo project
    if slug in demo_projects:
        from types import SimpleNamespace
        import datetime
        
        project_data = demo_projects[slug]
        project = SimpleNamespace(**project_data)
        project.created_at = datetime.datetime.now()
        
        developer = SimpleNamespace(**project_data['developer'])
        tech_stack = project_data.get('tech_stack', [])
        
        context = {
            'project': project,
            'developer': developer,
            'tech_stack': tech_stack,
            'user': request.user,
        }
        return render(request, 'core/project_detail.html', context)
    
    # Try to get from database
    try:
        project = Project.objects.get(url_slug=slug, visibility='public')
        project.views_count += 1
        project.save()
        
        developer = project.developer
        tech_stack = project.get_tech_stack_list()
        
        context = {
            'project': project,
            'developer': developer,
            'tech_stack': tech_stack,
            'user': request.user,
        }
        return render(request, 'core/project_detail.html', context)
        
    except Project.DoesNotExist:
        messages.error(request, f'Project not found.')
        return redirect('core:explore')

@login_required
def recruiter_post_job(request):
    """Recruiter post job page"""
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied. This area is for recruiters only.')
        return redirect('core:home')
    
    return render(request, 'recruiter/post_job.html', {'user': request.user})
