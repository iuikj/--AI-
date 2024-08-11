#
# # myapp/tasks.py
# from celery import shared_task
# from openai import OpenAI
#
# from AI.models import *
#
#
# @shared_task
# def send_message_task(command):
#     # 发送消息的逻辑
#     client = OpenAI()
#     thread_info: Threads = Threads.objects.first()
#     message = client.beta.threads.messages.create(
#         thread_id=thread_info.thread_id,
#         content=command,
#         role="user"
#     )
#     client.beta.threads.runs.create(
#         thread_id=thread_info.thread_id,
#         assistant_id=Assistants.objects.get(assistant_name="thread_info.thread_id"),
#     )
#     response = "Message sent: " + command
#     print("消息已发送")
#     return response

