from django.urls import re_path

from AI import consumers

websocket_urlpatterns = [
    re_path(r'^ai/(?P<group>\w+)/$', consumers.StreamConsumer.as_asgi()),
    re_path(r'^command_parse/(?P<group>\w+)/$', consumers.CommandParserConsumer.as_asgi()),
    re_path(r'^stream_AI_parser/(?P<group>\w+)/$', consumers.StreamConmmandParserConsumer.as_asgi()),
]
