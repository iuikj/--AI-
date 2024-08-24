from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        # 有客户端向后端发送websocket连接请求的时候自动自动触发
        # 服务端允许和客户端创建链接
        self.accept()

    def websocket_receive(self, message):
        # 浏览器基于websocket向后端发送数据，自动触发接收消息
        print(message)
        self.send("不要回复，不要回复，不要回复")
        # self.close()

    def websocket_disconnect(self, message):
        # 客户端与服务端断开连接，自动触发
        raise StopConsumer()