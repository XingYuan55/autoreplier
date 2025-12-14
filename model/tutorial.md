# 大语言模型函数调用教程

## 1. 基本概念

### 1.1 什么是函数调用

函数调用（Function Calling）允许语言模型：

- 理解用户的意图
- 选择合适的函数
- 提供正确的参数
- 处理函数返回的结果

### 1.2 工作流程

1. 用户输入问题
2. 模型理解并决定调用函数
3. 执行函数获取结果
4. 模型根据结果生成回答

## 2. 实现步骤

### 2.1 定义工具函数

    def get_weather_forecast(city: str, days: int = 1):
        """获取城市天气预报。

        Args:
            city: 城市名称，如"北京"、"上海"
            days: 预报天数，1-7天

        Returns:
            dict: 包含天气信息的字典
        """
        return {
            "city": city,
            "forecast": f"{city}未来{days}天天气晴朗"
        }

### 2.2 定义工具描述

我们需要为模型提供清晰的工具描述，让它知道如何使用这个函数：

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_weather_forecast",
                "description": get_weather_forecast.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        },
                        "days": {
                            "type": "integer",
                            "description": "预报天数"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]

### 2.3 实现函数调用处理

这是处理函数调用的核心部分：

    def chat(messages, params=None):
        try:
            # 1. 调用模型获取回复
            response = ollama.chat(
                model='qwen2.5:0.5b',
                messages=messages,
                tools=TOOLS,
                **params
            )

            # 2. 检查是否需要调用函数
            if tool_calls := response['message'].get('tool_calls'):
                results = []

                # 3. 处理每个函数调用
                for tool_call in tool_calls:
                    if fn_call := tool_call.get('function'):
                        # 获取函数名和参数
                        fn_name = fn_call['name']
                        fn_args = fn_call['arguments']

                        # 获取并执行函数
                        fn = globals().get(fn_name)
                        if fn:
                            result = fn(**fn_args)
                            results.append({
                                'role': 'tool',
                                'name': fn_name,
                                'content': json.dumps(result)
                            })

                # 4. 将结果添加到对话历史
                messages.extend(results)

                # 5. 再次调用模型生成最终回答
                final_response = ollama.chat(
                    model='qwen2.5:0.5b',
                    messages=messages,
                    tools=TOOLS,
                    **params
                )
                return final_response['message']['content']

            return response['message']['content']
        except Exception as e:
            return f"发生错误: {str(e)}"

## 3. 关键概念解释

### 3.1 海象运算符 `:=`

在代码中我们看到这样的用法：

    if tool_calls := response['message'].get('tool_calls'):

这是 Python 3.8 引入的海象运算符，它可以在条件判断时同时完成赋值。等价于：

    tool_calls = response['message'].get('tool_calls')
    if tool_calls:

### 3.2 全局函数获取

代码中使用了 `globals()` 来获取函数：

    fn = globals().get(fn_name)

- `globals()` 返回一个包含所有全局变量的字典
- `.get(fn_name)` 安全地获取函数对象，如果不存在返回 None
- 这样可以通过字符串名称动态调用函数

### 3.3 参数解包

在函数调用时使用了 `**` 操作符：

    result = fn(**fn_args)

这会将字典展开为关键字参数，例如：

- 字典：`{"city": "北京", "days": 1}`
- 展开后：`city="北京", days=1`

## 4. 数据结构

### 4.1 工具调用响应

当模型决定调用函数时，会返回如下结构：

    {
        "message": {
            "tool_calls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "get_weather_forecast",
                        "arguments": {
                            "city": "北京",
                            "days": 1
                        }
                    }
                }
            ]
        }
    }

### 4.2 消息历史格式

对话历史保存在 messages 列表中：

    messages = [
        {
            "role": "system",
            "content": "系统提示消息"
        },
        {
            "role": "user",
            "content": "用户输入"
        },
        {
            "role": "tool",
            "name": "函数名",
            "content": "函数返回结果"
        },
        {
            "role": "assistant",
            "content": "模型回复"
        }
    ]

## 5. 使用示例

### 5.1 基本使用

    # 导入必要的库
    import ollama
    import json

    # 初始化对话
    messages = [
        {
            "role": "system",
            "content": "你是一个助手，可以查询天气信息。"
        }
    ]

    # 用户提问
    user_input = "北京明天天气怎么样？"
    messages.append({"role": "user", "content": user_input})

    # 获取回复
    response = chat(messages)
    print(response)

### 5.2 完整对话流程

1. 用户发送问题
2. 模型理解需要天气信息
3. 调用 get_weather_forecast 函数
4. 获取结果并生成自然语言回答
5. 将整个过程记录在对话历史中

## 6. 注意事项

### 6.1 函数设计原则

- 函数名要清晰易懂
- 提供详细的文档字符串
- 参数类型和说明要明确
- 返回值格式要统一

### 6.2 错误处理

- 检查函数是否存在
- 处理参数解析错误
- 捕获函数执行异常
- 保持对话历史完整性

### 6.3 性能考虑

- 避免重复函数调用
- 合理设置对话历史长度
- 注意内存使用

## 7. 参考资料

- [Qwen 官方文档](https://qwen.readthedocs.io/)
- [Ollama Python API](https://github.com/ollama/ollama-python)
- [Python 函数调用文档](https://docs.python.org/3/reference/expressions.html#calls)

# 代码示例

def example():
print("Hello")

更多文本内容...
