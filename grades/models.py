from django.contrib.auth.models import User, Group
from django.db import models

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, default="")
    deadline = models.DateTimeField()
    weight = models.IntegerField()
    points = models.IntegerField()

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    grader = models.ForeignKey(User, related_name='graded_set', on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)