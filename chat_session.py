import time
from chat_window import ChatWindow

class ChatSession:
    """
    聊天会话管理器，提供更高级的消息交互功能。
    
    这个类在 ChatWindow 的基础上添加了：
    1. 消息状态管理
    2. 冷却时间控制
    3. 消息变化检测
    4. 完整的交互流程

    属性:
        window (ChatWindow): 聊天窗口实例
        cooldown (float): 发送消息的冷却时间（秒）
        last_content: 上次检测到的内容
        last_send_time: 上次发送消息的时间
        had_change: 是否检测到新消息
        stable_count: 消息稳定性计数
    """

    def __init__(self, window: ChatWindow, cooldown=2.0):
        self.window = window
        self.cooldown = cooldown
        self.last_content = None
        self.last_send_time = 0
        self.had_change = False
        self.stable_count = 0
        self.last_image = self.window.get_window_content()

    def check_new_message(self):
        """
        检查是否有新消息
        
        返回:
            bool: 是否检测到新消息
        """
        current_image = self.window.get_window_content()
        if not self.window.images_equal(current_image, self.last_image):
            self.last_image = current_image
            self.stable_count = 0
            return True
        return False

    def can_send_message(self):
        """检查是否可以发送消息（冷却时间）"""
        return time.time() - self.last_send_time > self.cooldown

    def wait_for_stable(self, required_stable_count=2):
        """
        等待内容稳定
        
        参数:
            required_stable_count: 需要保持稳定的检查次数
        
        返回:
            bool: 是否达到稳定状态
        """
        if not self.check_new_message():
            self.stable_count += 1
            return self.stable_count >= required_stable_count
        return False

    def copy_message(self, **kwargs):
        """
        复制消息并等待冷却
        
        参数:
            **kwargs: 传递给 ChatWindow.copy_message 的参数
        
        返回:
            str: 复制的内容
        """
        if not self.can_send_message():
            remaining = self.cooldown - (time.time() - self.last_send_time)
            self.window.log.log(f"冷却中，还需等待 {remaining:.1f} 秒")
            return ""

        content = self.window.copy_message(**kwargs)
        if content:
            self.last_send_time = time.time()
            self.had_change = True
        return content

    def send_message(self, message):
        """
        发送消息并更新状态
        
        参数:
            message: 要发送的消息
        
        返回:
            bool: 是否发送成功
        """
        if self.window.send_message(message):
            self.last_send_time = time.time()
            self.had_change = False
            return True
        return False

    def reset_state(self):
        """重置所有状态"""
        self.had_change = False
        self.stable_count = 0
        self.last_image = self.window.get_window_content() 