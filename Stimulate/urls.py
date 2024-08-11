"""
URL configuration for Stimulate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

import AI.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('AI/clean/', AI.views.clean),
    path('AI/message/send/', AI.views.send_message),
    path('AI/message/result', AI.views.get_message_results),
    path('AI/file/upload/function/', AI.views.upload_function_file),
    path('AI/file/upload/',AI.views.upload_file),
    path('AI/user/register/', AI.views.register),
    path('AI/user/login/', AI.views.login),
]
