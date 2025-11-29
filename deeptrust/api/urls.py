from django.urls import path
from .views import verify_media, job_status, job_report

urlpatterns = [
    path("verify/", verify_media),
    path("status/<str:job_id>/", job_status),
    path("report/<str:job_id>/", job_report),
]
