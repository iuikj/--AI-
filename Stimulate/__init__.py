
# myproject/__init__.py
from __future__ import absolute_import, unicode_literals

# 这将确保 Django 启动时加载应用程序的 celery.py 模块
from .celery import app as celery_app

__all__ = ('celery_app',)

