import pyautogui
import threading
import time
import pygetwindow as gw
from PIL import Image
import win32clipboard  
import logs
import json
import atexit
from model.inference import chat  # 导入本地模型接口

pyautogui.FAILSAFE = True

class AiAutoReplier:
    """
    自动回复器类，用于监控微信消息并通过AI自动回复
    
    属性:
        wx_send_coordinate: 微信发送框的坐标
        wx_reply_coordinate: 微信消息区域的坐标
        wx_reply_window: 微信窗口的监控区域 [(x1,y1), (x2,y2)]
        wx_had_changed: 微信消息是否已处理的标记
    """

    def __init__(self):
        settings = self.load_settings()
        # 只保留微信相关坐标
        self.wx_send_coordinate = settings["wx_send_coordinate"]
        self.wx_reply_coordinate = settings["wx_reply_coordinate"]
        self.wx_reply_window = settings["wx_reply_window"]
        
        self.wx_had_changed = False
        
        # 分开存储系统提示和示例消息
        self.system_prompt = {
            "role": "system",
            "content": settings["model.ai_system_prompt"]
        }
        self.examples = settings.get("model.message_examples", [])
        
        # 初始化对话历史
        self.message_history = []
        
        self.message_memory_rounds = settings["model.message_memory_rounds"]
        
        self.log = logs.logging()
        
        self.thread_monitor_window = threading.Thread(target=self.monitor_window, daemon=True)
        self.thread_monitor_window.start()

        # 注册退出时的回调函数
        atexit.register(self.save_message_history)

        # 添加上下文管理
        self.context = {
            "time_of_day": self.get_time_period(),
            "last_topic": None,
            "conversation_start_time": time.time()
        }

    def get_window_content(self, region):
        """
        截取指定区域的图像
        
        参数:
            region: 要截取的区域坐标 [(x1,y1), (x2,y2)]
        
        返回:
            PIL.Image: 截取的图像对象
        """
        x1, y1 = region[0]
        x2, y2 = region[1]
        screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        return screenshot

    def simulate_copy(self):
        """
        模拟复制操作
        
        功能:
            使用三击选中文本并复制到剪贴板
        """
        pyautogui.click(clicks=3)  # 三击选中文本
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)

    def simulate_paste_and_send(self):
        """
        模拟粘贴和发送操作
        
        功能:
            将剪贴板内容粘贴并按回车发送
        """
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        pyautogui.press('enter')

    def monitor_window(self):
        """监控微信窗口变化的主循环"""
        check_interval = 1
        last_wx_img = self.get_window_content(self.wx_reply_window)
        last_send_time = time.time()
        cooldown_period = 2

        while True:
            try:
                time.sleep(check_interval)
                current_time = time.time()
                
                # 检查微信窗口变化
                current_wx_img = self.get_window_content(self.wx_reply_window)
                
                if not self.images_equal(current_wx_img, last_wx_img) and not self.wx_had_changed:
                    time_diff = current_time - last_send_time
                    self.log.log(f"时间差: {time_diff:.2f}秒")
                    
                    if time_diff > cooldown_period:
                        self.log.log("检测到微信窗口变化", level="state")
                        if self.handle_message():
                            last_send_time = time.time()
                        last_wx_img = current_wx_img
                    else:
                        self.log.log(f"冷却中，还需等待 {cooldown_period - time_diff:.2f}秒")
                        last_wx_img = current_wx_img

            except pyautogui.FailSafeException:
                self.log.log("程序已通过故障安全机制停止", "key")
                raise

    def images_equal(self, img1, img2):
        """
        比较两张图片是否相同
        
        参数:
            img1: 第一张图片
            img2: 第二张图片
        
        返回:
            bool: 图片是否相同
        """
        return list(img1.getdata()) == list(img2.getdata())

    def get_clipboard_content(self):
        """
        获取剪贴板中的文本内容
        
        返回:
            str: 剪贴板中的文本，如果不是文本则返回空字符串
        """
        try:
            win32clipboard.OpenClipboard()
            try:
                # 首先尝试 Unicode 格式
                try:
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    if data and data.strip():
                        return data
                except:
                    pass

                # 如果 Unicode 失败，尝试普通文本格式
                try:
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    # 尝试多种编码方式
                    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
                    for encoding in encodings:
                        try:
                            text = data.decode(encoding)
                            if text.strip():
                                return text
                        except:
                            continue
                except:
                    pass

                return ""
            finally:
                win32clipboard.CloseClipboard()
        except:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return ""

    def clear_clipboard(self):
        """清空剪贴板内容"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
        except:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

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
            "娱乐": ["游戏", "电影", "音乐", "运动"],
            # 可以添加更多主题
        }
        
        for topic, words in keywords.items():
            if any(word in message for word in words):
                return topic
        return None
        
    def handle_message(self):
        """处理新消息并使用本地模型回复"""
        try:
            # 获取微信消息
            self.clear_clipboard()
            pyautogui.moveTo(self.wx_reply_coordinate[0], self.wx_reply_coordinate[1])
            time.sleep(0.3)
            pyautogui.doubleClick()
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            message = self.get_clipboard_content()
            if not message.strip():
                self.log.log("未检测到文本内容，可能是表情或图片，跳过处理", level="state")
                return False
                
            self.log.log(f"收到消息: {message}")
            
            # 分析主题并维持连续性
            current_topic = self.analyze_topic(message)
            if current_topic and current_topic == self.context["last_topic"]:
                # 如果主题连续，添加连续性提示
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
            self.message_history.append({"role": "user", "content": message})  # 添加用户消息
            last_n = max(len(self.message_history) - self.message_memory_rounds, 0)
            messages_to_send = [self.system_prompt] + self.examples + self.message_history[last_n:]
            
            self.log.log(f'模型对话历史传入：{str(messages_to_send)}', "model")
            response = chat(messages_to_send)
            
            # 只将实际对话添加到历史记录
            self.message_history.append({"role": "assistant", "content": response})
            
            # 发送回复
            pyautogui.moveTo(self.wx_send_coordinate[0], self.wx_send_coordinate[1])
            time.sleep(0.2)
            pyautogui.click()
            time.sleep(0.2)
            
            # 将回复写入剪贴板并发送
            self.set_clipboard_text(response)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            pyautogui.press('enter')
            
            self.log.log(f"已回复: {response}")
            return True
            
        except pyautogui.FailSafeException:
            self.log.log("检测到安全停止信号", "key")
            raise  # 重新抛出 FailSafeException
        except Exception as e:
            self.log.log(f"处理消息时出错: {e}", "error")
            return False

    def set_clipboard_text(self, text):
        """设置剪贴板文本内容"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

    def load_settings(self):
        with open('settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def start(self):
        """
        启动自动回复程序
        
        功能:
        1. 启动监控线程
        2. 保持程序运行
        3. 处理程序终止信号
        
        终止方式:
        - Ctrl+C
        - 将鼠标移动到屏幕角落
        """
        self.log.log("自动回复程序已启动...", "key")
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, pyautogui.FailSafeException):
            self.log.log("程序已停止", "key")
            exit(0)

    def save_message_history(self):
        """在程序退出时保存对话历史"""
        try:
            self.log.log("程序退出，保存对话历史...", "key")
            self.log.log(f"完整对话历史：{str(self.message_history)}", "model")
            self.log.log(f"最终日志已保存", "key")
        except:
            pass  # 确保这个函数不会抛出异常

if __name__ == "__main__":
    replier = AiAutoReplier()
    replier.start()

