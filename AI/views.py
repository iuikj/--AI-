import json
import os
import random
import string
from contextlib import ExitStack
from io import BytesIO

from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

from AI.models import *
from Stimulate import settings


def upload_file(request):
    if request.method == 'GET':
        return render(request, "uploadFile_to_OpenAI.html")
    elif request.method == 'POST':
        # 这是一个InMemoryUploadedFile类型对象，是Django处理文件上传的类型且是存储在内存而非磁盘中的
        file_object = request.FILES['file']
        # 将文件写入项目的指定文件夹
        file_path = os.path.join(settings.BASE_DIR, 'AI', 'files', 'function_file.txt')

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        print(file_path)

        file_content = file_object.read()
        file_io = BytesIO(file_content)

        ## 这里不选择写入文件到磁盘中
        # with open(file_path,"wb") as f:
        #     for chunk in file_object.chunks():
        #         f.write(chunk)

        client = OpenAI()
        file = client.files.create(
            file=(file_object.name, file_io),
            purpose="assistants",
        )
        print(file_io.__sizeof__())
        Files.objects.create(file_id=file.id, file_name=file_object.name, file_size=file_io.__sizeof__())
        return HttpResponse("ok")


def upload_function_file(request):
    # 上传文件到OpenAI的文件存储，并在本地的数据库存档
    client = OpenAI()
    if request.method == 'GET':
        print("转到网页")
        return render(request, "uploadFile.html")
    elif request.method == 'POST':
        file_object = request.FILES.get("function_file")
        if not file_object:
            return HttpResponseBadRequest("没有文件上传")

        file_path = "function_file.txt"
        with open(file_path, "wb") as f:
            for chunk in file_object.chunks():
                f.write(chunk)

        vector_store = client.beta.vector_stores.create(
            name="模拟控制函数"
        )

        # 准备要上传到向量存储的文件
        files_arr = [file_path, ]

        try:
            # 使用 ExitStack 来管理多个上下文管理器并确保它们被正确关闭
            with ExitStack() as stack:
                # 以二进制读取模式打开每个文件，并将文件流添加到列表中
                file_streams = [stack.enter_context(open(file, "rb")) for file in files_arr]

                # 使用上传和轮询助手方法上传文件，将它们添加到向量存储，并轮询文件批次的状态直到完成
                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id, files=file_streams
                )

            # 将向量存储附加到助理以启用文件搜索功能
            assistant = client.beta.assistants.update(
                assistant_id=Assistants.objects.get(assistant_name="模拟-智慧家庭AI助手-全屋助手").assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            print("助理工具:")
            for tool in assistant.tools:
                print(f" - {tool}")

            # 打印助理的工具资源以验证向量存储的附加
            print("\n助理工具资源:")
            for resource, details in assistant.tool_resources:
                print(f" - {resource}: {details}")

        except Exception as e:
            print(f"更新助理时发生错误: {e}")

        return HttpResponse("上传成功")


@csrf_exempt
# Create your views here.
def send_message(request):
    command_str: str = None

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            command_str = data['command_message']
        except (KeyError, json.JSONDecodeError):
            return HttpResponseBadRequest("Invalid JSON data or missing 'command' parameter")

    client = OpenAI()
    # 获取当前登录的用户信息，目前发送指令默认发送到默认的进程中
    u_id = request.session.get("user_id")

    # 获取默认的进程
    threads = Threads.objects.filter(user_id_id=u_id).all()
    selected_thread_id = None
    for thread in threads:
        if thread.purpose == "默认/全屋管家":
            selected_thread_id = thread.thread_id

    assistant = Assistants.objects.filter(user_id_id=u_id).get(assistant_name="模拟-智慧家庭AI助手-全屋助手")
    message = client.beta.threads.messages.create(
        thread_id=selected_thread_id,
        content=command_str,
        role="user"
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=selected_thread_id,
        assistant_id=assistant.assistant_id
    )

    request.session["fresh_run_id"] = run.id
    request.session["thread_id"] = selected_thread_id
    return redirect(get_message_results)


@csrf_exempt
def get_message_results(request):
    client = OpenAI()
    response_data: dict = {}
    fresh_run_id = request.session["fresh_run_id"]
    thread_id = request.session["thread_id"]
    latest_assistant_message = None
    for message in client.beta.threads.messages.list(thread_id=thread_id):
        if message.role == "assistant" and message.run_id == fresh_run_id:
            latest_assistant_message = message

    if latest_assistant_message:
        response_data["code"] = 200
        response_data["message"] = "成功生成回复"
        response_data["data"] = [json.loads(latest_assistant_message.content[0].text.value)]
        print("输出回复:\n" + latest_assistant_message.content[0].text.value)
        return JsonResponse(response_data)
    else:
        response_data["code"] = 500,
        response_data["message"] = "出现错误"
        print("未找到该助手的消息")
        return JsonResponse(response_data)


def clean(request):
    client = OpenAI()
    if request.GET["target"] == "assistant":
        all_assistant = client.beta.assistants.list()
        for assistant in all_assistant:
            if assistant.name == "模拟-智慧家庭AI助手-全屋助手":
                client.beta.assistants.delete(assistant.id)

    Assistants.objects.filter(assistant_name="模拟-智慧家庭AI助手-全屋助手").delete()

    return HttpResponse(status=200)


@csrf_exempt
def register(request):
    # 这个函数是用来注册新用户的，用户模型Users对应数据库表中的Users(此数据库可能部署在后端，后续待修改)
    # 故此函数仅做测试使用
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username: str = data["username"]
            password: str = data["password"]
            # 此处使用随机字符串来模拟区块链上的独有身份信息
            characters: str = string.ascii_letters + string.digits
            # 从字符集中随机选择字符，并组合成指定长度的字符串
            random_string = ''.join(random.choices(characters, k=10))

            print("----------------")
            print(f"注册信息：\n")
            print(f"用户名{username}\n")
            print(f"密码{password}\n")
            print(f"身份Id{random_string}\n")

            Users.objects.create(username=username, password=password, user_id=random_string)
            print("注册成功")
            result_data = {
                'result': '注册成功'
            }
            return JsonResponse(result_data)
        except Exception as e:
            print(f"错误信息：{e}"
                  )
            return JsonResponse(
                {
                    'result': '注册失败'
                }
            )


@csrf_exempt
def login(request):
    def init_assistant_with_vector_store(u: Users):
        client = OpenAI()
        assistants = Assistants.objects.select_related("user_id").all()

        flag: bool = False
        for assistant in assistants:
            if assistant.user_id_id == u.user_id:
                flag = True

        # 当对应用户已经创建了对应助手了，则不做任何操作
        if not flag:
            # 如果是第一次登录（数据库中无用户对应的初始助手）
            print("第一次登录，暂无助手，初始化助手")

            prompt = """
                                               你是一个软件——智慧家庭，的AI助手。你负责接受用户自然语言命令，并能够将语句中的命令解析理解出准确的对智能家居的操作指令。在理解命令的时候你应该遵循以下步骤：

                                               第一，分解出语义中的：指令发起人、指令的操作对象、指令本身的操作行为（如开灯、关灯、开锁、设置烤箱预约等）。第二，在分析出上述信息后捕获出语义中指令操作的对应参数（如烤箱预约时间：“30分钟”，开启“客厅”的灯并将亮度调为“70%”等等。）。第三，通过上述信息在矢量库中上传的文件中寻找最合适匹配的函数信息（包括函数名，参数列表，参数名称等等）。最后，将你处理得到的信息按照下面的

                                               模版按照json格式输出：
                                               {
                                                   "functionName": "fun",
                                                   "params": [
                                                       {
                                                           {
                                                               "paramName": "param1(参数名)",
                                                               "paramType": "参数类型",
                                                               "value": "参数的值"
                                                           }
                                                       },
                                                       {
                                                            {
                                                               "paramName": "参数名称（对象）",
                                                               "paramType": "参数类型（对象）",
                                                               "values（对象参数的各成员变量的值）": [
                                                                   {
                                                                       "name": "light",
                                                                       "type": "int",
                                                                       "value": 50
                                                                   },
                                                                   {
                                                                       "name": "a",
                                                                       "type": "str",
                                                                       "value": "0"
                                                                   }
                                                               ]
                                                           }
                                                       }
                                                   ]
                                               }
                                               """

            assistant = client.beta.assistants.create(
                name="模拟-智慧家庭AI助手-全屋助手",
                model="gpt-4o-mini",
                instructions=prompt,
                tools=[
                    {"type": "file_search"}
                ],
                metadata=
                {
                    "name": u.username,
                    "isInit": "True"
                }
            )
            vector_store = client.beta.vector_stores.create(
                file_ids=[Files.objects.get(file_name="Trc01.txt").file_id],
                name="文档存储",
                metadata={
                    "username": u.username,
                    "isInit": "True"
                }
            )

            # 将vector_store存入数据库
            v = VectorStores.objects.create(vector_store_id=vector_store.id, vector_store_name=vector_store.name)
            client.beta.assistants.update(
                assistant_id=assistant.id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            print("assistant id:", assistant.id)
            print("所属用户:", u.username)
            Assistants.objects.create(assistant_id=assistant.id, assistant_name=assistant.name,
                                      attached_vector_store_id=v,
                                      information="初始化的全屋智能助手", user_id=u)

    def init_thread(u: Users):
        client = OpenAI()
        threads = Threads.objects.filter(user_id=u.user_id)
        # 如果没有找到，返回一个空的QuerySet
        if not threads.exists():
            thread = client.beta.threads.create(
                metadata={
                    "username": u.username,
                    "isInit": "True"
                }
            )
            print(f"初始化，新的默认进程:{thread.id}")
            Threads.objects.create(
                user_id=u,
                thread_id=thread.id,
                purpose="默认/全屋管家"
            )

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data["username"]
            password = data["password"]
            user = Users.objects.get(username=username, password=password)
            if user is not None:
                request.session["user_id"] = user.user_id
                print(f"登录成功，用户：{user.username}")
                result_data = {
                    'result': '登录成功'
                }
                try:
                    init_assistant_with_vector_store(user)
                    init_thread(user)
                except Exception as e:
                    print(f"初始化异常：{e}")
                return JsonResponse(result_data)
            else:
                result_data = {
                    'result': '登录失败'
                }
                print("登录失败，用户名或密码错误")
                return JsonResponse(result_data)
        except Exception as e:
            print(e)
