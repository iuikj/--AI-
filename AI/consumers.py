import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
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