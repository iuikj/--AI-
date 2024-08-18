import os
from celery import Celery


# 把celery和Django结合，识别和加载Django的配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Stimulate.settings')

# 创建celery实例对象
app = Celery('DjCelery_AI')

# 通过app对象加载配置
app.config_from_object('AI_celery.config')

# 加载任务
# 参数必须是列表，里面美格任务都是任务的路径名称
app.autodiscover_tasks(["AI_celery.message"])

# 启动Celery的命令
# celery -A mycelery.main worker -l info
# 建议在此项目的根目录下启动