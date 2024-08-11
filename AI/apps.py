from django.apps import AppConfig


def init_assitant():
    from openai import OpenAI
    from AI.models import Assistants
    client = OpenAI()
    if not Assistants.objects.exists():
        print("暂无助手，初始化助手")

        prompt = """
                                    你是一个软件——智慧家庭，的AI助手。你负责接受用户自然语言命令，并能够将语句中的命令解析理解出准确的对智能家居的操作指令。在理解命令的时候你应该遵循以下步骤：

                                    第一，分解出语义中的：指令发起人、指令的操作对象、指令本身的操作行为（如开灯、关灯、开锁、设置烤箱预约等）。第二，在分析出上述信息后捕获出语义中指令操作的对应参数（如烤箱预约时间：“30分钟”，开启“客厅”的灯并将亮度调为“70%”等等。）。第三，通过上述信息在矢量库中上传的文件中寻找最合适匹配的函数信息（包括函数名，参数列表，参数名称等等）。最后，将你处理得到的信息按照下面的

                                    模版按照json格式输出：
                                    {
                                        "functionName": "fun",
                                        "params": [
                                            {
                                                "param1(参数1,与参数名一致)": {
                                                    "paramName": "param1(参数名)",
                                                    "paramType": "参数类型",
                                                    "value": "参数的值"
                                                }
                                            },
                                            {
                                                "param2(参数2)": {
                                                    "paramName": "参数名称（对象）",
                                                    "paramType": "参数类型（对象）",
                                                    "value（对象参数的各成员变量的值）": {
                                                        "light": {
                                                            "name": "light",
                                                            "type": "int"
                                                        },
                                                        "a": {
                                                            "name": "a",
                                                            "type": "str"
                                                        }
                                                    }
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
                    "name": "test",
                    "isInit": "True"
                }
        )
        print("assistant id:", assistant.id)
        Assistants.objects.create(assistant_id=assistant.id, assistant_name=assistant.name,
                                  information="初始化的全屋智能助手")


def init_thread():
    from openai import OpenAI
    from AI.models import Threads
    client = OpenAI()
    if not Threads.objects.exists():
        print("暂无线程，初始化线程供测试对话使用")
        thread = client.beta.threads.create(
            metadata={
                "name": "test",
                "isInit": "True"
            }
        )
        print("thread id:", thread)
        Threads.objects.create(thread_id=thread.id)


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'AI'

    def ready(self):
        init_assitant()
        init_thread()
