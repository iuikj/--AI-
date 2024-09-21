import json
from rest_framework.authtoken.models import Token

from AI.models import Threads, Assistants
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from django.http import JsonResponse
from openai import OpenAI, AsyncOpenAI

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import AsyncOpenAI


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.assistant_id = None
        self.thread_id = None
        print("AI-连接成功")
        await self.accept()

    async def disconnect(self, close_code):
        # close_code用来判断关闭的原因，其设计待定
        print("AI-连接断开")
        self.assistant_id = None
        self.thread_id = None

    async def receive(self, text_data):
        print("AI-接收到消息数据", text_data)
        data = json.loads(text_data)
        prompt = data.get('prompt')
        print("AI-接收到消息", prompt)
        # 调用 run_openai_task 来处理流式输出
        await self.run_openai_task(prompt)

    async def run_openai_task(self, prompt):
        async for chunk in self.stream_openai_response(prompt):
            # print(chunk)
            await self.send(text_data=json.dumps({
                'message': chunk
            }))
        print("任务完成")

    async def stream_openai_response(self, prompt):
        print("开始生成回答")
        client = AsyncOpenAI()

        # 创建 Assistant 实例（每个连接有独立的 Assistant）
        if not self.assistant_id:
            assistant = await client.beta.assistants.create(
                name="测试异步",
                model="gpt-4o-mini",
            )
            self.assistant_id = assistant.id

        # 创建一个会话线程（每个连接有独立的线程）
        if not self.thread_id:
            thread = await client.beta.threads.create()
            self.thread_id = thread.id

        # 向线程发送消息
        await client.beta.threads.messages.create(
            content=prompt,
            role="user",
            thread_id=self.thread_id
        )

        # 开始运行任务，并启用流式输出
        run = await client.beta.threads.runs.create(
            assistant_id=self.assistant_id,
            thread_id=self.thread_id,
            stream=True,  # 启用流式输出
        )

        # 这里 run 应该返回一个异步生成器，可以直接用 async for 迭代
        async for event in run:
            if hasattr(event.data, 'status'):  # 检查事件数据是否有 'status' 属性
                print(event.data.id)
                print(event.data.status)
            else:
                print(f"事件 ID: {event.data.id} 没有 status 属性。")
                if hasattr(event.data, 'delta') and event.data.delta:
                    for block in event.data.delta.content:
                        text = block.text.value
                        print(text)
                        yield text  # 使用 yield 返回每个数据块
            print("---------------\n")


from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
from channels.db import database_sync_to_async


class CommandParserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("CommandParser-连接成功")
        await self.accept()

    async def disconnect(self, close_code):
        print("CommandParser-连接断开")
        await self.close()

    async def receive(self, text_data):
        print("CommandParser-接收到消息数据", text_data)
        data = json.loads(text_data)
        command = data.get('command_message')  # 获取命令消息
        print("CommandParser-接收到命令", command)
        # 调用 run_command_parser 来处理命令
        await self.run_command_parser(data)

    async def run_command_parser(self, command_data):
        # 调用命令解析器，解析命令，并返回结果
        result = await self.parse_command(command_data)
        await self.send(text_data=json.dumps(result))

    @database_sync_to_async
    def get_token_user(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            print("token_key无效")
            return None

    @database_sync_to_async
    def get_threads(self, user_id):
        return list(Threads.objects.filter(user_id_id=user_id).all())

    @database_sync_to_async
    def get_assistant(self, user_id):
        return Assistants.objects.get(user_id_id=user_id, assistant_name="模拟-智慧家庭AI助手-全屋助手")

    async def parse_command(self, command_data):
        command = command_data.get('command_message')

        # # 获取session数据
        # session = self.scope["session"]
        # print("CommandParser-获取session数据", session)
        # u_id = session.get('user_id', None)
        # print("CommandParser-获取用户ID", u_id)

        # 在websocket获取token_key
        token_key = self.scope['query_string'].decode('utf-8').split('=')[1]
        print(self.scope['query_string'].decode('utf-8'))
        print("CommandParser-获取token_key", token_key)
        user = await self.get_token_user(token_key=token_key)
        print("CommandParser-获取用户", user)

        print("CommandParser-获取用户ID", user.user_id)
        # 异步获取默认的进程
        threads = await sync_to_async(list)(Threads.objects.filter(user_id_id=user.user_id).all())
        selected_thread_id = None
        for thread in threads:
            if thread.purpose == "默认/全屋管家":
                selected_thread_id = thread.thread_id

        # 异步获取助手信息
        assistant = await sync_to_async(Assistants.objects.get)(user_id_id=user.user_id,
                                                                assistant_name="模拟-智慧家庭AI助手-全屋助手")

        client = AsyncOpenAI()

        # 异步调用消息创建API
        message = await client.beta.threads.messages.create(
            thread_id=selected_thread_id,
            content=command,
            role="user"
        )

        # 异步调用运行创建和轮询API
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=selected_thread_id,
            assistant_id=assistant.assistant_id
        )

        response_data = {}
        fresh_run_id = run.id
        thread_id = selected_thread_id
        latest_assistant_message = None

        # 异步获取消息列表
        async for message in client.beta.threads.messages.list(thread_id=thread_id):
            if message.role == "assistant" and message.run_id == fresh_run_id:
                latest_assistant_message = message

        if latest_assistant_message:
            response_data["code"] = 200
            response_data["message"] = "成功生成回复"
            print("输出回复:\n" + latest_assistant_message.content[0].text.value.encode('utf-8').decode('utf-8'))
            result_message = latest_assistant_message.content[0].text.value

            # 分解字符串为JSON数据交由后端去执行
            start_marker = "`json"
            end_marker = "`"
            start_index = result_message.find(start_marker)
            end_index = None
            if start_index != -1:
                start_index += len(start_marker)
                end_index = result_message.find(end_marker, start_index)

            if start_index != -1 and end_index != -1:
                parsed_message = result_message[start_index:end_index].strip()
                print(f"解析出来的字符串：{parsed_message}")
                response_data["data"] = [json.loads(parsed_message)]
            else:
                response_data["code"] = 500
                response_data["message"] = "解析助手消息失败"

            return response_data
        else:
            response_data["code"] = 500
            response_data["message"] = "未找到助手的消息"
            print("未找到该助手的消息")
            return response_data


class StreamConmmandParserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("StreamConmmandParser-连接成功")
        self.assistant_id = None
        self.thread_id = None

    async def disconnect(self, close_code):
        print("AI-连接断开")
        self.assistant_id = None
        self.thread_id = None

    async def receive(self, text_data):
        print("StreamConmmandParser-接收到消息数据", text_data)
        data = json.loads(text_data)
        command = data.get('command_message')  # 获取命令消息
        print("StreamConmmandParser-接收到命令", command)
        # 调用 run_command_parser 来处理命令
        await self.run_command_parser_stream(data)

    @database_sync_to_async
    def get_token_user(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            print("token_key无效")
            return None
    async def run_command_parser_stream(self, command_data):
        # 调用命令解析器，解析命令，并返回结果

        async for chunk in self.parse_command_stream(command_data):
            # 这里逐步解析流式输出的消息，将解析出来的json代码返回给后端，将解析的格式化信息返回给前端并动态生成页面
            await self.send(text_data=json.dumps({
                'message': chunk
            }))
        print("任务完成")

    async def parse_command_stream(self, command_data):
        # 在websocket获取token_key
        command: str = command_data.get('command_message')
        token_key = self.scope['query_string'].decode('utf-8').split('=')[1]
        print("StreamCommandParser-获取token_key", token_key)
        user = await self.get_token_user(token_key=token_key)
        print("StreamCommandParser-获取用户", user)

        print("StreamCommandParser-获取用户ID", user.user_id)
        # 异步获取默认的进程
        threads = await sync_to_async(list)(Threads.objects.filter(user_id_id=user.user_id).all())
        selected_thread_id = None
        for thread in threads:
            if thread.purpose == "默认/全屋管家":
                selected_thread_id = thread.thread_id

        # 异步获取助手信息
        assistant = await sync_to_async(Assistants.objects.get)(user_id_id=user.user_id,
                                                                assistant_name="模拟-智慧家庭AI助手-全屋助手")

        client = AsyncOpenAI()

        # 异步调用消息创建API
        message = await client.beta.threads.messages.create(
            thread_id=selected_thread_id,
            content=command,
            role="user"
        )

        # 异步调用运行创建和轮询API
        run = await client.beta.threads.runs.create(
            thread_id=selected_thread_id,
            assistant_id=assistant.assistant_id,
            stream=True,  # 启用流式输出
        )

        async for event in run:
            if hasattr(event.data, 'status'):  # 检查事件数据是否有 'status' 属性
                print(event.data.id)
                print(event.data.status)
            else:
                print(f"事件 ID: {event.data.id} 没有 status 属性。")
                if hasattr(event.data, 'delta') and event.data.delta :
                    if hasattr(event.data.delta,'content') and event.data.delta.content:
                        for block in event.data.delta.content:
                            text = block.text.value
                            print(text)
                            yield text  # 使用 yield 返回每个数据块
                    # for block in event.data.delta:
                    #     # text = block.text.value
                    #     print(f"测试内容：---->{block.__class__}")
                    #     print(block)
                    #     yield 1  # 使用 yield 返回每个数据块
            print("---------------\n")
