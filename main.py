import pyautogui
import threading
import time
import pygetwindow as gw
from PIL import Image
import win32clipboard  # 添加此导入

pyautogui.FAILSAFE = True  # 启用故障安全（移动到角落可以终止）

class AiAutoReplier:
    """
    自动回复器类，用于监控微信消息并通过AI自动回复
    
    属性:
        ai_reply_coordinate: AI回复区域的坐标
        ai_send_coordinate: AI发送框的坐标
        wx_send_coordinate: 微信发送框的坐标
        wx_reply_coordinate: 微信消息区域的坐标
        ai_reply_window: AI回复窗口的监控区域 [(x1,y1), (x2,y2)]
        wx_reply_window: 微信窗口的监控区域 [(x1,y1), (x2,y2)]
        wx_had_changed: 微信消息是否已处理的标记
        ai_had_changed: AI回复是否已处理的标记
        ai_stable_count: AI窗口稳定性计数器
    """

    def __init__(self):
        self.ai_reply_coordinate = (147, 845)
        self.ai_send_coordinate = (166, 977)
        self.wx_send_coordinate = (994, 877)
        self.wx_reply_coordinate = (1049, 792)

        self.ai_reply_window = [(337, 120), (350, 400)]
        self.wx_reply_window = [(1040, 300), (1300, 820)]

        self.wx_had_changed = False
        self.ai_had_changed = False
        
        # 初始化并启动监控线程
        self.thread_monitor_window = threading.Thread(target=self.monitor_window, daemon=True)
        self.thread_monitor_window.start()

        self.last_ai_content = None
        self.ai_stable_count = 0

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
        """
        监控窗口变化的主循环
        
        功能:
        1. 检测微信窗口变化，处理新消息
        2. 检测AI窗口变化，处理回复
        3. 管理冷却时间，防止频繁操作
        4. 控制处理流程的状态转换
        """
        check_interval = 1
        last_wx_img = self.get_window_content(self.wx_reply_window)
        last_ai_img = self.get_window_content(self.ai_reply_window)
        self.ai_stable_count = 0
        last_send_time = time.time()
        cooldown_period = 2

        while True:
            try:
                time.sleep(check_interval)
                current_time = time.time()
                
                # 检查微信窗口变化
                current_wx_img = self.get_window_content(self.wx_reply_window)
                current_ai_img = self.get_window_content(self.ai_reply_window)
                
                # 如果微信窗口有新消息且不在冷却期间
                if not self.images_equal(current_wx_img, last_wx_img) and not self.wx_had_changed:
                    time_diff = current_time - last_send_time
                    print(f"时间差: {time_diff:.2f}秒")
                    
                    # 检查是否已经过了冷却期
                    if time_diff > cooldown_period:
                        print("检测到微信窗口变化")
                        if self.handle_wx_message():  # 修改：检查处理结果
                            self.wx_had_changed = True
                            self.ai_had_changed = False
                            self.ai_stable_count = 0
                        last_wx_img = current_wx_img
                        time.sleep(0.5)
                    else:
                        print(f"冷却中，还需等待 {cooldown_period - time_diff:.2f}秒")
                        last_wx_img = current_wx_img
                
                # 只有在等待AI回复时才检查AI窗口
                elif self.wx_had_changed and not self.ai_had_changed:
                    if not self.images_equal(current_ai_img, last_ai_img):
                        print("AI窗口正在变化...")
                        last_ai_img = current_ai_img
                        self.ai_stable_count = 0
                    else:
                        self.ai_stable_count += 1
                        if self.ai_stable_count == 2:
                            print("AI回复已稳定，准备处理回复")
                            self.handle_ai_response()
                            last_ai_img = current_ai_img
                            self.ai_had_changed = True
                            self.wx_had_changed = False
                            self.ai_stable_count = 0
                            last_send_time = time.time()
                            print(f"更新发送时间戳: {last_send_time:.2f}")

            except pyautogui.FailSafeException:
                print("程序已通过故障安全机制停止")
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
                data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                return data.decode('utf-8') if data else ""
            except:
                return ""
            finally:
                win32clipboard.CloseClipboard()
        except:
            return ""

    def handle_wx_message(self):
        """
        处理微信新消息
        
        功能:
        1. 选中并复制微信消息
        2. 检查是否成功复制到文本内容
        3. 将内容发送到AI聊天框
        
        返回:
            bool: 处理是否成功
        """
        try:
            # 先移动到微信消息位置
            pyautogui.moveTo(self.wx_reply_coordinate[0], self.wx_reply_coordinate[1])
            time.sleep(0.3)
            
            # 双击选中微信消息
            pyautogui.doubleClick()
            time.sleep(0.2)
            
            # 复制选中的内容
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            # 检查是否成功复制到内容
            clipboard_content = self.get_clipboard_content()
            if not clipboard_content.strip():
                print("未检测到文本内容，可能是表情或图片，跳过处理")
                return False  # 返回False表示处理失败
            
            # 有文本内容，继续处理
            pyautogui.moveTo(self.ai_send_coordinate[0], self.ai_send_coordinate[1])
            time.sleep(0.2)
            pyautogui.click()
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            pyautogui.press('enter')
            print("微信消息已发送到AI")
            return True  # 返回True表示处理成功
            
        except pyautogui.FailSafeException:
            raise
        except Exception as e:
            print(f"处理微信消息时出错: {e}")
            return False  # 出错时返回False

    def handle_ai_response(self):
        """
        处理AI的回复
        
        功能:
        1. 选中并复制AI的回复
        2. 将回复发送到微信聊天框
        
        异常:
            捕获并处理可能的异常，确保程序稳定运行
        """
        try:
            # 点击AI回复区域并三击选中
            pyautogui.moveTo(self.ai_reply_coordinate[0], self.ai_reply_coordinate[1])
            time.sleep(0.3)
            pyautogui.click(clicks=3)
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.3)
            
            # 切换到微信窗口并粘贴发送
            pyautogui.moveTo(self.wx_send_coordinate[0], self.wx_send_coordinate[1])
            time.sleep(0.2)
            pyautogui.click()
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            pyautogui.press('enter')
            print("AI回复已发送到微信")
        except pyautogui.FailSafeException:
            raise
        except Exception as e:
            print(f"处理AI回复时出错: {e}")

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
        print("自动回复程序已启动...")
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, pyautogui.FailSafeException):
            print("程序已停止")
            exit(0)

if __name__ == "__main__":
    replier = AiAutoReplier()
    replier.start()


