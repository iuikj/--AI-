from django.db import models


# Create your models here.
class Assistants(models.Model):
    assistant_id = models.CharField(max_length=40, primary_key=True)
    assistant_name = models.CharField(max_length=100)
    information = models.CharField(max_length=100)
    attached_vector_store_id = models.ForeignKey("VectorStores", on_delete=models.CASCADE, null=True, blank=True)
    user_id = models.ForeignKey("Users", on_delete=models.CASCADE, null=True, blank=True)


class VectorStores(models.Model):
    vector_store_id = models.CharField(max_length=40, primary_key=True)
    vector_store_name = models.CharField(max_length=100)
    information = models.CharField(max_length=100)
    user_id = models.ForeignKey("Users", on_delete=models.CASCADE, null=True, blank=True)


class Files(models.Model):
    file_id = models.CharField(max_length=40, primary_key=True)
    file_name = models.CharField(max_length=100)
    file_size = models.IntegerField()
    information = models.CharField(max_length=100)


class Threads(models.Model):
    thread_id = models.CharField(max_length=40, primary_key=True)
    video_store_id = models.ForeignKey("VectorStores", on_delete=models.CASCADE, null=True, blank=True)
    user_id = models.ForeignKey("Users", on_delete=models.CASCADE, null=True, blank=True)
    purpose = models.CharField(max_length=50)


class Messages(models.Model):
    message_id = models.CharField(max_length=40, primary_key=True)
    thread_id = models.ForeignKey("Threads", on_delete=models.CASCADE)


class Runs(models.Model):
    run_id = models.CharField(max_length=40, primary_key=True)
    thread_id = models.ForeignKey("Threads", on_delete=models.CASCADE)
    assistant_id = models.ForeignKey("Assistants", on_delete=models.CASCADE)


class Users(models.Model):
    user_id = models.CharField(max_length=40, primary_key=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
