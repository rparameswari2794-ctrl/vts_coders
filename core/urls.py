# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Existing URLs
    path('', views.common_home, name='home'),
    path('explore/', views.explore_page, name='explore'),
    path('developers/', views.developers_page, name='developers'),
    path('job-listings/', views.job_listings_page, name='joblisting'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/developer/', views.developer_signup, name='developer_signup'),
    path('signup/recruiter/', views.recruiter_signup, name='recruiter_signup'),
    
    # Developer URLs
    path('developer/home/', views.developer_home, name='developer_home'),
    path('developer/joblisting/', views.my_projects, name='developer_joblisting'),
    path('developer/profile/', views.developer_profile, name='developer_profile'),
    path('developer/explore/', views.developer_explore_page, name='developer_explore'),
    path('developer/developer/', views.developer_developers_page, name='developer_developers'),
    
    # Project Upload URLs
    path('developer/upload-project/step1/', views.upload_project_step1, name='upload_project_step1'),
    path('developer/upload-project/step2/', views.upload_project_step2, name='upload_project_step2'),
    path('developer/upload-project/step3/', views.upload_project_step3, name='upload_project_step3'),
    path('developer/upload-project/step4/', views.upload_project_step4, name='upload_project_step4'),
    path('developer/save-project/', views.save_project, name='save_project'),
    path('developer/projects-api/', views.developer_projects_api, name='developer_projects_api'),
    path('developer/project-preview/', views.project_preview, name='project_preview'),
    
    # Profile URLs
    path('developer/profile/form/', views.developer_profile_form, name='developer_profile_form'),
    path('developer/profile/edit/', views.developer_profile_edit, name='developer_profile_edit'),
    
    # Recruiter URLs
    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('recruiter/home/', views.recruiter_home, name='recruiter_home'),
    path('recruiter/explore/', views.recruiter_explore, name='recruiter_explore'),
    path('recruiter/developers/', views.recruiter_developers, name='recruiter_developers'),
    path('recruiter/profile/', views.recruiter_profile, name='recruiter_profile'),
    path('recruiter/post/', views.recruiter_post_job, name='recruiter_post_job'),
    
    # Admin URLs
    path('recruiter/list/', views.recruiter_list, name='recruiter_list'),
    
    # API URLs
    path('api/developers-list/', views.developers_list_api, name='developers_list_api'),
    path('api/recruiters-list/', views.recruiters_list_api, name='recruiters_list_api'),
    path('api/all-users/', views.get_all_users, name='get_all_users'),
    
    # CHAT API URLs - IMPORTANT: These must be defined
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
    path('api/messages/send/', views.send_message, name='send_message'),
    path('api/messages/mark-read/<int:conversation_id>/', views.mark_messages_read, name='mark_messages_read'),
    
    # Chat page
    path('chat/', views.chat_page, name='chat'),
    # Project detail URL
    path('project/<slug:slug>/', views.project_detail, name='project_detail'),
]