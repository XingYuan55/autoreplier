# 导入必要的库
from wxauto import WeChat  # wxauto库的核心类
import time  # 用于添加延时和时间戳
import logs  # 项目中的日志模块

class WxHandler:
    """
    基于wxauto的微信消息处理器，提供高级的消息交互功能。
    
    这个类封装了wxauto库的功能，并添加了消息状态管理、冷却控制、变化检测等功能，
    使得消息交互更加稳定和智能，层次上与ChatSession等同。

    主要功能：
    1. 消息状态管理：跟踪消息的变化和稳定状态
    2. 冷却时间控制：防止消息发送过于频繁
    3. 消息变化检测：智能检测新消息
    4. 完整的交互流程：包括获取、发送等操作的状态管理

    属性：
        wx (WeChat): wxauto的WeChat实例，处理具体的微信操作
        current_contact (str): 当前聊天的联系人
        cooldown (float): 发送消息的冷却时间（秒）
        last_messages (dict): 各联系人的上次消息记录
        last_send_time (float): 上次发送消息的时间戳
        had_change (bool): 是否检测到新消息
        stable_count (int): 消息稳定性计数
    """
    
    def __init__(self, contact=None, cooldown=2.0):
        # 初始化微信实例，这会连接到当前打开的微信窗口
        self.wx = WeChat()
        self.current_contact = contact
        self.cooldown = cooldown
        self.last_messages = {}
        self.last_send_time = 0
        self.had_change = False
        self.stable_count = 0
        
        if contact:
            # 如果提供了联系人名称，尝试切换到该联系人的聊天窗口
            self.wx.ChatWith(contact)
            # 等待切换完成
            time.sleep(0.5)
            # 初始化该联系人的最后消息记录
            self.last_messages[contact] = self.get_last_message()
            
        # 获取日志记录器
        self.log = logs.logging()
        # 记录初始化成功的日志
        self.log.log("微信处理器初始化成功")
    
    def switch_contact(self, contact):
        """
        切换到指定联系人的聊天窗口
        
        参数:
            contact (str): 联系人名称
            
        返回:
            bool: 是否切换成功
        """
        try:
            self.wx.ChatWith(contact)
            time.sleep(0.5)  # 等待切换完成
            self.current_contact = contact
            
            # 如果是首次切换到该联系人，初始化最后消息记录
            if contact not in self.last_messages:
                self.last_messages[contact] = self.get_last_message()
                
            self.log.log(f"切换到联系人: {contact}")
            return True
        except Exception as e:
            self.log.log(f"切换联系人失败: {e}", "error")
            return False
    
    def can_send_message(self):
        """检查是否可以发送消息（冷却时间）"""
        return time.time() - self.last_send_time > self.cooldown
    
    def send_message(self, message, contact=None):
        """
        发送消息并更新状态
        
        这个方法会：
        1. 检查冷却时间
        2. 切换联系人（如果需要）
        3. 发送消息
        4. 更新状态
        
        参数:
            message (str): 要发送的消息内容
            contact (str): 接收消息的联系人名称
            
        返回:
            bool: 是否发送成功
        """
        # 检查冷却时间
        if not self.can_send_message():
            remaining = self.cooldown - (time.time() - self.last_send_time)
            self.log.log(f"冷却中，还需等待 {remaining:.1f} 秒")
            return False
            
        try:
            # 如果提供了联系人且与当前不同，切换联系人
            if contact and contact != self.current_contact:
                if not self.switch_contact(contact):
                    return False
                    
            # 发送消息
            self.wx.SendMsg(message)
            
            # 更新状态
            self.last_send_time = time.time()
            self.had_change = False  # 重置变化状态
            
            # 记录日志
            self.log.log(f"发送消息到 {self.current_contact}: {message}")
            return True
        except Exception as e:
            # 记录错误日志
            self.log.log(f"发送消息失败: {e}", "error")
            return False
    
    def get_last_message(self, contact=None):
        """
        获取指定联系人的最新消息
        
        参数:
            contact (str): 联系人名称
            
        返回:
            str: 最新消息内容，如果没有则返回空字符串
        """
        try:
            # 如果提供了联系人且与当前不同，切换联系人
            if contact and contact != self.current_contact:
                if not self.switch_contact(contact):
                    return ""
                    
            # 获取所有消息
            messages = self.wx.GetAllMessage()
            
            # 检查是否有消息
            if messages and len(messages) > 0:
                # 返回最后一条消息
                last_msg = messages[-1]
                return last_msg
            return ""
        except Exception as e:
            # 记录错误日志
            self.log.log(f"获取消息失败: {e}", "error")
            return ""
    
    def check_new_message(self, contact=None):
        """
        检查指定联系人是否有新消息
        
        参数:
            contact (str): 联系人名称
            
        返回:
            bool: 是否有新消息
            str: 新消息内容（如果有）
        """
        try:
            # 如果提供了联系人且与当前不同，切换联系人
            if contact and contact != self.current_contact:
                if not self.switch_contact(contact):
                    return False, ""
            
            # 获取当前最新消息
            current_msg = self.get_last_message()
            
            # 如果联系人不在记录中，初始化并返回False
            if self.current_contact not in self.last_messages:
                self.last_messages[self.current_contact] = current_msg
                return False, ""
            
            # 比较最新消息与上次记录的消息
            last_msg = self.last_messages[self.current_contact]
            
            # 如果消息不同，更新记录并返回True
            if current_msg != last_msg and current_msg:
                self.last_messages[self.current_contact] = current_msg
                self.stable_count = 0
                self.had_change = True
                return True, current_msg
            
            return False, ""
        except Exception as e:
            self.log.log(f"检查新消息失败: {e}", "error")
            return False, ""
    
    def wait_for_stable(self, required_stable_count=2):
        """
        等待内容稳定
        
        参数:
            required_stable_count: 需要保持稳定的检查次数
        
        返回:
            bool: 是否达到稳定状态
        """
        has_new, _ = self.check_new_message()
        if not has_new:
            self.stable_count += 1
            return self.stable_count >= required_stable_count
        return False
    
    def reset_state(self):
        """重置所有状态"""
        self.had_change = False
        self.stable_count = 0
        # 重新获取当前联系人的最新消息
        if self.current_contact:
            self.last_messages[self.current_contact] = self.get_last_message()
    
    def monitor_changes(self, contact=None, check_interval=1.0):
        """
        监控指定联系人的消息变化，是消息处理的核心方法
        
        这个方法会：
        1. 检查是否有新消息
        2. 追踪消息的稳定性
        3. 管理冷却时间
        4. 记录状态变化
        
        参数：
            contact (str): 联系人名称
            check_interval (float): 检查间隔时间（秒）
            
        返回：
            str: 监控状态
                - "changed": 检测到新消息
                - "stable": 消息已稳定
                - "cooling": 正在冷却
                - "unchanged": 无变化
                - "error": 发生错误
            str: 新消息内容（如果有）
        """
        try:
            # 如果提供了联系人且与当前不同，切换联系人
            if contact and contact != self.current_contact:
                if not self.switch_contact(contact):
                    return "error", ""
            
            # 检查是否有新消息
            has_new, new_msg = self.check_new_message()
            
            if has_new:
                # 只有当状态从稳定变为不稳定时才记录日志
                if not self.had_change:
                    self.log.log(f"{self.current_contact} 有新消息...", level="state")
                return "changed", new_msg
            
            # 检查是否稳定
            if self.had_change:
                self.stable_count += 1
                if self.stable_count >= 2:  # 2次检查，确保真的稳定
                    self.had_change = False
                    return "stable", new_msg
            
            # 检查冷却时间
            if not self.can_send_message():
                remaining = self.cooldown - (time.time() - self.last_send_time)
                self.log.log(f"冷却中，还需等待 {remaining:.1f} 秒")
                return "cooling", ""
            
            return "unchanged", ""
        
        except Exception as e:
            self.log.log(f"监控出错: {e}", "error")
            return "error", ""
    
    def get_contacts(self):
        """
        获取联系人列表
        
        返回:
            list: 联系人列表
        """
        try:
            return self.wx.GetContacts()
        except Exception as e:
            self.log.log(f"获取联系人列表失败: {e}", "error")
            return []