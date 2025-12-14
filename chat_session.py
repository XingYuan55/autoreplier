import time
from chat_window import ChatWindow

class ChatSession:
    """
    聊天会话管理器，提供高级的消息交互功能。
    
    这个类在 ChatWindow 的基础上添加了消息状态管理、冷却控制、变化检测等功能，
    使得消息交互更加稳定和智能。

    主要功能：
    1. 消息状态管理：跟踪窗口内容的变化和稳定状态
    2. 冷却时间控制：防止消息发送过于频繁
    3. 消息变化检测：智能检测窗口内容的变化
    4. 完整的交互流程：包括复制、发送等操作的状态管理

    属性：
        window (ChatWindow): 聊天窗口实例，处理具体的窗口操作
        cooldown (float): 发送消息的冷却时间（秒）
        last_content: 上次检测到的内容
        last_send_time (float): 上次发送消息的时间戳
        had_change (bool): 是否检测到新消息
        stable_count (int): 消息稳定性计数
        last_image: 上次截取的窗口图像

    使用示例：
        # 创建一个聊天窗口实例
        window = ChatWindow(
            send_coordinate=[100, 500],
            reply_coordinate=[100, 400],
            reply_window=[[50, 300], [150, 450]],
            name="WeChat"
        )
        
        # 创建会话管理器
        session = ChatSession(window, cooldown=2.0)
        
        # 监控变化
        while True:
            status = session.monitor_changes()
            if status == "stable":
                # 窗口内容稳定，可以处理消息
                content = session.copy_message()
                if content:
                    session.send_message(f"回复：{content}")
            
            time.sleep(1)  # 避免过于频繁的检查

    监控状态说明：
        - "changed": 检测到新变化，内容不稳定
        - "stable": 内容已稳定，可以进行操作
        - "cooling": 正在冷却中，需要等待
        - "unchanged": 无变化，继续监控
        - "error": 发生错误

    注意事项：
        1. 使用前需要正确配置 ChatWindow 的坐标参数
        2. 建议根据实际需求调整 cooldown 和稳定性检查次数
        3. 所有操作都有日志记录，方便调试
        4. 状态变化和错误都会记录到日志
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
        复制消息并管理状态
        
        这个方法会：
        1. 检查冷却时间
        2. 调用窗口的复制功能
        3. 更新状态
        
        参数：
            **kwargs: 传递给 ChatWindow.copy_message 的参数
                clicks (int): 点击次数
                copy_by_button (bool): 是否使用复制按钮
        
        返回：
            str: 复制的内容，失败返回空字符串
        
        使用示例：
            # 普通复制
            content = session.copy_message(clicks=2)
            
            # 使用复制按钮
            content = session.copy_message(copy_by_button=True)
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
        
        这个方法会：
        1. 调用窗口的发送功能
        2. 更新发送时间
        3. 重置变化状态
        
        参数：
            message (str): 要发送的消息
        
        返回：
            bool: 是否发送成功
        
        使用示例：
            if session.send_message("你好"):
                print("发送成功")
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

    def monitor_changes(self, check_interval=1.0):
        """
        监控窗口变化，是消息处理的核心方法
        
        这个方法会：
        1. 检查窗口内容是否发生变化
        2. 追踪内容的稳定性
        3. 管理冷却时间
        4. 记录状态变化
        
        参数：
            check_interval (float): 检查间隔时间（秒）
            
        返回：
            str: 监控状态
                - "changed": 检测到新变化
                - "stable": 内容已稳定
                - "cooling": 正在冷却
                - "unchanged": 无变化
                - "error": 发生错误
        
        使用示例：
            status = session.monitor_changes()
            if status == "stable":
                # 可以处理消息了
                content = session.copy_message()
        """
        try:
            current_image = self.window.get_window_content()
            
            # 检查是否有变化
            if not self.window.images_equal(current_image, self.last_image):
                # 只有当状态从稳定变为不稳定时才记录日志
                if not self.had_change:
                    self.window.log.log(f"{self.window.name} 窗口正在变化...", level="state")
                self.last_image = current_image
                self.stable_count = 0
                self.had_change = True
                return "changed"
            
            # 检查是否稳定
            if self.had_change:
                self.stable_count += 1
                if self.stable_count >= 2:  # 改回2次检查，确保真的稳定
                    self.had_change = False
                    return "stable"
            
            # 检查冷却时间
            if not self.can_send_message():
                remaining = self.cooldown - (time.time() - self.last_send_time)
                self.window.log.log(f"{self.window.name} 冷却中，还需等待 {remaining:.1f} 秒")
                return "cooling"
                
            return "unchanged"
            
        except Exception as e:
            self.window.log.log(f"{self.window.name} 监控出错: {e}", "error")
            return "error" 