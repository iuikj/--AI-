from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
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


# class Users(models.Model):
#     user_id = models.CharField(max_length=40, primary_key=True)
#     username = models.CharField(max_length=100)
#     password = models.CharField(max_length=100)


# MyUserManager 负责用户的创建，包含两个方法：create_user 用于创建普通用户，create_superuser 用于创建管理员用户。
# create_user: 这个方法用于创建普通用户，确保用户名必填并设置密码。
# create_superuser: 这个方法在创建超级用户时使用，确保is_staff和is_superuser为True。
class MyUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)


# AbstractBaseUser: 提供基础的用户认证功能，但不包括权限管理。
# PermissionsMixin: 提供了与权限相关的功能，如支持is_superuser字段。
# 改造使用了Django自带的用户模型，并添加了is_active和is_staff字段。
class Users(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=50, primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    # is_active: 标记用户是否活跃，这个字段可用于禁用用户账号。
    # is_host: 标记用户是否为家庭主人，这个字段可用于限制用户的权限。
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()

    # USERNAME_FIELD 定义了哪个字段将用于用户登录，在此案例中为username。
    # REQUIRED_FIELDS 定义了除了USERNAME_FIELD和password之外，创建超级用户时必须填写的字段名。由于在这个模型中，username是唯一必填的，所以REQUIRED_FIELDS是空的。
    # 后续要修改为user_id，即did来作为登录凭证。
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
