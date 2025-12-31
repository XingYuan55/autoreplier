import threading
import time
import pyautogui
import logs
import json
import atexit
from model.inference import chat
from chat_core.chat_window import ChatWindow
from chat_core.chat_session import ChatSession

pyautogui.FAILSAFE = True

class AiAutoReplier:
    """
    自动回复器类，使用本地模型处理消息
    
    属性:
        wx_session: 微信会话管理器
        message_history: 对话历史记录
        message_memory_rounds: 记忆轮数
        context: 对话上下文信息
    """

    def __init__(self):
        settings = self.load_settings()
        
        # 创建微信会话
        self.wx_session = ChatSession(
            ChatWindow(
                send_coordinate=settings["wx_send_coordinate"],
                reply_coordinate=settings["wx_reply_coordinate"],
                reply_window=settings["wx_reply_window"],
                name="WeChat"
            )
        )
        
        # 分开存储系统提示和示例消息
        self.system_prompt = {
            "role": "system",
            "content": settings["model.ai_system_prompt"]
        }
        self.examples = settings.get("model.message_examples", [])
        
        # 初始化对话历史和设置
        self.message_history = []
        self.message_memory_rounds = settings["model.message_memory_rounds"]
        
        self.log = logs.logging()
        
        # 添加上下文管理
        self.context = {
            "time_of_day": self.get_time_period(),
            "last_topic": None,
            "conversation_start_time": time.time()
        }
        
        # 启动监控线程
        self.thread_monitor_window = threading.Thread(target=self.monitor_window, daemon=True)
        self.thread_monitor_window.start()

        # 注册退出时的回调函数
        atexit.register(self.save_message_history)

    def monitor_window(self):
        """监控微信窗口变化的主循环"""
        while True:
            try:
                time.sleep(1)
                
                # 监控微信窗口
                status = self.wx_session.monitor_changes()
                if status == "stable":
                    self.log.log("检测到微信窗口变化", level="state")
                    self.handle_message()

            except pyautogui.FailSafeException:
                self.log.log("程序已通过故障安全机制停止", "key")
                raise

    def get_time_period(self):
        """获取当前时间段"""
        hour = time.localtime().tm_hour
        if 5 <= hour < 12:
            return "早上"
        elif 12 <= hour < 14:
            return "中午"
        elif 14 <= hour < 18:
            return "下午"
        else:
            return "晚上"

    def analyze_topic(self, message):
        """简单的主题分析"""
        keywords = {
            "学习": ["考试", "作业", "课程", "学习", "复习"],
            "生活": ["吃饭", "睡觉", "天气", "心情"],
            "娱乐": ["游戏", "电影", "音乐", "运动"]
        }
        
        for topic, words in keywords.items():
            if any(word in message for word in words):
                return topic
        return None

    def handle_message(self):
        """处理新消息并使用本地模型回复"""
        try:
            # 获取微信消息
            message = self.wx_session.copy_message(clicks=2)
            if not message.strip():
                self.log.log("未检测到文本内容，可能是表情或图片，跳过处理", level="state")
                return False
                
            self.log.log(f"收到消息: {message}")
            
            # 分析主题并维持连续性
            current_topic = self.analyze_topic(message)
            if current_topic and current_topic == self.context["last_topic"]:
                self.message_history.append({
                    "role": "system",
                    "content": f"继续关于{current_topic}的话题"
                })
            self.context["last_topic"] = current_topic
            
            # 根据上下文调整系统提示
            current_time = self.get_time_period()
            if current_time != self.context["time_of_day"]:
                self.context["time_of_day"] = current_time
                time_prompt = f"现在是{current_time}，"
                self.message_history.append({
                    "role": "system",
                    "content": time_prompt
                })
            
            # 构建完整的消息列表
            self.message_history.append({"role": "user", "content": message})
            last_n = max(len(self.message_history) - self.message_memory_rounds, 0)
            messages_to_send = [self.system_prompt] + self.examples + self.message_history[last_n:]
            
            self.log.log(f'模型对话历史传入：{str(messages_to_send)}', "model")
            response = chat(messages_to_send)
            
            # 只将实际对话添加到历史记录
            self.message_history.append({"role": "assistant", "content": response})
            
            # 发送回复
            return self.wx_session.send_message(response)
            
        except pyautogui.FailSafeException:
            raise
        except Exception as e:
            self.log.log(f"处理消息时出错: {e}", "error")
            return False

    def load_settings(self):
        with open('settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_message_history(self):
        """在程序退出时保存对话历史"""
        try:
            self.log.log("程序退出，保存对话历史...", "key")
            self.log.log(f"完整对话历史：{str(self.message_history)}", "model")
        except:
            pass

    def start(self):
        """启动自动回复程序"""
        self.log.log("自动回复程序已启动...", "key")
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, pyautogui.FailSafeException):
            self.log.log("程序已停止", "key")
            exit(0)

if __name__ == "__main__":
    replier = AiAutoReplier()
    replier.start()

