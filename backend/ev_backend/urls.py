"""
Root URL Configuration
----------------------
This is the MAIN router of the entire Django project.

How URLs work in Django:
  Browser/Postman sends a request to → http://localhost:8000/api/auth/login/
  Django reads this file → sees prefix 'api/' → routes to core/urls.py
  core/urls.py → sees 'auth/login/' → calls the correct view function

We also serve uploaded media files (station images) during development.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin Panel → http://localhost:8000/admin/
    # You can view/edit all database records here (very useful for debugging!)
    path('admin/', admin.site.urls),

    # All our API routes → http://localhost:8000/api/...
    # This delegates everything starting with 'api/' to core/urls.py
    path('api/', include('core.urls')),
]

# Serve uploaded images (station photos) during development
# In production, a web server like Nginx would handle this.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
