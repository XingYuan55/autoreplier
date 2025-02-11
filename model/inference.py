import ollama
import json

MODEL = 'qwen2.5:1.5b'

def chat(messages, params=None):
    # 调整默认参数使回复更自然
    default_params = {
        'options': {
            'temperature': 0.8,    # 提高温度使输出更有创造性
            'top_p': 0.95,        # 略微提高采样范围
            'top_k': 50,          # 增加候选token数量
            'num_predict': 512,    # 保持不变
        }
    }
    # 如果传入了参数，更新默认参数
    if params:
        default_params['options'].update(params)
    
    try:
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            **default_params  # 现在参数在 options 字典中
        )
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
            "content": "你是我的同学，名叫王涵，学识渊博，语气温和，平易近人，现在正在与你聊天。"
        }
    ]
    
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() == 'quit':  break
        if not user_input:  continue
        
        messages.append({"role": "user", "content": user_input})
        print("\nQwen: ", end="")
        response = chat(messages[0]+messages[-10:])  # 传入整个消息历史
        print(response)
        messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main() 