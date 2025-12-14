import ollama
import json

MODEL = 'qwen2.5:1.5b'

def chat(messages, params=None):
    # 默认参数
    default_params = {
        'options': {
            'temperature': 0.7,    # 控制随机性 (0-1)
            'top_p': 0.9,         # 控制采样范围
            'top_k': 40,          # 控制候选token数量
            'num_predict': 512,    # 最大生成长度
        }
    }
    # 如果传入了参数，更新默认参数
    if params:
        default_params['options'].update(params)
    
    try:
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,  # 添加工具定义
            **default_params  # 现在参数在 options 字典中
        )

        # 检查是否有工具调用
        if tool_calls := response['message'].get('tool_calls'):
            results = []
            for tool_call in tool_calls:
                if fn_call := tool_call.get('function'):
                    fn_name = fn_call['name']
                    fn_args = fn_call['arguments']
                    
                    # 获取并执行函数
                    fn = globals().get(fn_name)
                    if fn:
                        # 执行函数调用
                        result = fn(**fn_args)
                        results.append({
                            'role': 'tool',
                            'name': fn_name,
                            'content': json.dumps(result)
                        })
            
            # 将工具调用结果添加到消息历史
            messages.extend(results)
            
            # 构建一个总结性提示
            summary_message = {
                "role": "user",
                "content": "请根据上述温度信息，用自然语言总结天气情况。"
            }
            messages.append(summary_message)
            
            # 获取最终回答
            final_response = ollama.chat(
                model='qwen2.5:1.5b',
                messages=messages,
                **default_params  # 不需要再传tools参数
            )
            return final_response['message']['content']
        
        # 如果没有工具调用，直接返回原始回答
        return response['message']['content']
    except Exception as e:
        return f"发生错误: {str(e)}"

def main():
    # 可以自定义参数
    print("开始对话，输入 'quit' 退出")
    messages = [
        {
            "role": "system",
            "content": "你是通义千问助手，由阿里云开发。请用友好自然的方式回答问题。"
        }
    ]
    
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() == 'quit':  break
        if not user_input:  continue
        
        messages.append({"role": "user", "content": user_input})
        print("\nQwen: ", end="")
        response = chat(messages)  # 传入整个消息历史
        print(response)
        messages.append({"role": "assistant", "content": response})

def get_current_temperature(location: str, unit: str = "celsius"):
    """获取指定位置的当前温度。

    Args:
        location: 城市名称，如"北京"、"上海"等
        unit: 温度单位，默认为 "celsius"。可选值: ["celsius", "fahrenheit"]

    Returns:
        包含温度、位置和单位的字典
    """
    return {
        "temperature": 26.1,
        "location": location,
        "unit": unit,
    }

def get_temperature_date(location: str, date: str, unit: str = "celsius"):
    """获取指定位置和日期的温度。

    Args:
        location: 城市名称，如"北京"、"上海"等
        date: 要获取温度的日期，格式为 "Year-Month-Day"
        unit: 温度单位，默认为 "celsius"。可选值: ["celsius", "fahrenheit"]

    Returns:
        包含温度、位置、日期和单位的字典
    """
    return {
        "temperature": 25.9,
        "location": location,
        "date": date,
        "unit": unit,
    }

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_temperature",
            "description": "获取指定位置的当前温度",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'等",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": '温度单位，默认为 "celsius"',
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_temperature_date",
            "description": "获取指定位置和日期的温度",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'等",
                    },
                    "date": {
                        "type": "string",
                        "description": '要获取温度的日期，格式为 "Year-Month-Day"',
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": '温度单位，默认为 "celsius"',
                    },
                },
                "required": ["location", "date"],
            },
        },
    },
]

if __name__ == "__main__":
    main() 