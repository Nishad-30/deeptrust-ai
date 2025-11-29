from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

class VerificationJob(models.Model):
    job_id = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    media_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, default="processing")
    result_ready = models.BooleanField(default=False)
    truth_cert_id = models.CharField(max_length=256, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)      # existing field
    created_at = models.DateTimeField(auto_now_add=True)       # new canonical time
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_id} - {self.media_id} - {self.status}"


class TruthCertificate(models.Model):
    certificate_id = models.CharField(max_length=100, unique=True)
    media_id = models.CharField(max_length=100)
    job = models.ForeignKey(VerificationJob, on_delete=models.CASCADE)
    truthscore = models.IntegerField()
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_path = models.TextField()

    def __str__(self):
        return self.certificate_id
