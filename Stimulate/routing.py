from django.urls import re_path

from AI import consumers

websocket_urlpatterns = [
    # xxxxx/room/x1 就会走这个
    re_path(r'room/(?P<group>\w+)/$', consumers.ChatConsumer.as_asgi()),
]