import threading
import time
import pyautogui
import logs
import json
from chat_window import ChatWindow
from chat_session import ChatSession

pyautogui.FAILSAFE = True

class AiAutoReplier:
    def __init__(self):
        settings = self.load_settings()
        
        # 创建聊天会话
        self.wx_session = ChatSession(
            ChatWindow(
                send_coordinate=settings["wx_send_coordinate"],
                reply_coordinate=settings["wx_reply_coordinate"],
                reply_window=settings["wx_reply_window"],
                name="WeChat"
            )
        )
        
        self.ai_session = ChatSession(
            ChatWindow(
                send_coordinate=settings["ai_send_coordinate"],
                reply_coordinate=settings["ai_reply_coordinate"],
                reply_window=settings["ai_reply_window"],
                name="AI"
            ),
            cooldown=3.0  # AI可能需要更长的冷却时间
        )
        
        self.wx_had_changed = False
        self.ai_had_changed = False
        self.ai_stable_count = 0
        
        self.log = logs.logging()
        
        self.thread_monitor_window = threading.Thread(target=self.monitor_window, daemon=True)
        self.thread_monitor_window.start()

    def monitor_window(self):
        check_interval = 1.0

        while True:
            try:
                time.sleep(check_interval)
                
                # 监控微信窗口
                wx_status = self.wx_session.monitor_changes()
                if wx_status == "stable" and not self.wx_had_changed:
                    self.log.log("检测到微信窗口变化", level="state")
                    if self.handle_wx_message():
                        self.wx_had_changed = True
                        self.ai_had_changed = False
                
                # 监控AI窗口
                if self.wx_had_changed and not self.ai_had_changed:
                    ai_status = self.ai_session.monitor_changes()
                    if ai_status == "stable":
                        self.log.log("AI回复已稳定，准备处理回复", level="state")
                        self.handle_ai_response()
                        self.ai_had_changed = True
                        self.wx_had_changed = False

            except pyautogui.FailSafeException:
                self.log.log("程序已通过故障安全机制停止", "key")
                raise

    def handle_wx_message(self):
        """处理微信新消息"""
        try:
            content = self.wx_session.copy_message(clicks=2)  # 微信用双击
            if not content.strip():
                self.log.log("未检测到文本内容，可能是表情或图片，跳过处理", level="state")
                self.wx_had_changed = False
                return False
            
            return self.ai_session.send_message(content)
            
        except pyautogui.FailSafeException:
            raise
        except Exception as e:
            self.log.log(f"处理微信消息时出错: {e}", "error")
            self.wx_had_changed = False
            return False

    def handle_ai_response(self):
        """处理AI的回复"""
        try:
            content = self.ai_session.copy_message(copy_by_button=True)  # 使用复制按钮
            if content:
                self.wx_session.send_message(content)
        except pyautogui.FailSafeException:
            raise
        except Exception as e:
            self.log.log(f"处理AI回复时出错: {e}", "error")

    def load_settings(self):
        with open('settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def start(self):
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

