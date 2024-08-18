# mycelery/config.py

# 设置结果后端为 Redis
result_backend = 'redis://:000000@127.0.0.1:6379/3'

# 设置 broker 为 Redis
broker_url = 'redis://:000000@127.0.0.1:6379/4'


from AI_celery.main import app

app.conf.worker_redirect_stdouts = True
app.conf.worker_redirect_stdouts_level = 'INFO'
