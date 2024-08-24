from django.urls import re_path

from AI import consumers

websocket_urlpatterns = [
    re_path(r'^ai/(?P<group>\w+)/$', consumers.StreamConsumer.as_asgi())
]
