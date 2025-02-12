import pyautogui
import time
import win32clipboard
from PIL import Image
import logs

class ChatWindow:
    """
    聊天窗口操作接口，提供通用的窗口操作功能。
    
    这个类封装了对聊天窗口的基本操作，包括消息的监控、复制和发送。
    它使用 pyautogui 进行窗口操作，支持中英文文本处理。

    属性:
        send_coordinate (list): 发送框的坐标 [x, y]
        reply_coordinate (list): 消息区域的坐标 [x, y]
        reply_window (list): 监控区域 [(x1,y1), (x2,y2)]
        name (str): 窗口标识名（用于日志）
        log (logs.logging): 日志记录器实例

    示例:
        # 创建一个微信窗口实例
        wx_window = ChatWindow(
            send_coordinate=[100, 500],
            reply_coordinate=[100, 400],
            reply_window=[[50, 300], [150, 450]],
            name="WeChat"
        )

        # 发送消息
        wx_window.send_message("你好")

        # 获取新消息
        content = wx_window.copy_message()

    注意:
        1. 使用前确保窗口在正确位置
        2. 坐标值需要根据实际屏幕分辨率调整
        3. 操作间有适当的延时以确保稳定性
    """

    def __init__(self, send_coordinate, reply_coordinate, reply_window, name="ChatWindow"):
        self.send_coordinate = send_coordinate
        self.reply_coordinate = reply_coordinate
        self.reply_window = reply_window
        self.name = name
        self.log = logs.logging()

    def get_window_content(self):
        """截取监控区域的图像"""
        x1, y1 = self.reply_window[0]
        x2, y2 = self.reply_window[1]
        return pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))

    def images_equal(self, img1, img2):
        """比较两张图片是否相同"""
        return list(img1.getdata()) == list(img2.getdata())

    def get_clipboard_content(self):
        """获取剪贴板中的文本内容"""
        try:
            win32clipboard.OpenClipboard()
            try:
                # 尝试 Unicode 格式
                try:
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    if data and data.strip():
                        return data
                except:
                    pass

                # 尝试普通文本格式
                try:
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
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

    def copy_message(self, clicks=2, copy_by_button=False):
        """
        复制消息区域的内容
        
        参数:
            clicks (int): 选中文本需要的点击次数
                - 1: 单击（用于复制按钮）
                - 2: 双击选中单行文本（默认）
                - 3: 三击选中整段文本
            copy_by_button (bool): 是否通过点击复制按钮来复制
                - True: 直接点击复制按钮
                - False: 使用选中文本并复制的方式（默认）
        
        返回:
            str: 复制的文本内容，失败则返回空字符串
        """
        try:
            self.clear_clipboard()
            pyautogui.moveTo(self.reply_coordinate[0], self.reply_coordinate[1])
            time.sleep(0.3)
            
            if copy_by_button:
                pyautogui.click()
                time.sleep(0.5)  # 等待复制完成
            else:
                pyautogui.click(clicks=clicks)
                time.sleep(0.3)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                
            content = self.get_clipboard_content()
            self.log.log(f"{self.name} 复制内容: [{content}]")
            return content
        except Exception as e:
            self.log.log(f"{self.name} 复制消息失败: {e}", "error")
            return ""

    def send_message(self, message):
        """发送消息"""
        try:
            pyautogui.moveTo(self.send_coordinate[0], self.send_coordinate[1])
            time.sleep(0.2)
            pyautogui.click()
            time.sleep(0.2)
            
            # 将消息写入剪贴板并发送
            self.clear_clipboard()
            win32clipboard.OpenClipboard()
            win32clipboard.SetClipboardText(message, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            pyautogui.press('enter')
            self.log.log(f"{self.name} 发送消息: {message}")
            return True
        except Exception as e:
            self.log.log(f"{self.name} 发送消息失败: {e}", "error")
            return False

    def copy_by_button(self):
        """
        通过点击复制按钮来复制内容
        
        这个方法适用于有专门复制按钮的界面（如AI聊天网页）
        
        返回:
            str: 复制的文本内容，失败则返回空字符串
        """
        try:
            self.clear_clipboard()
            # 点击复制按钮位置
            pyautogui.moveTo(self.reply_coordinate[0], self.reply_coordinate[1])
            time.sleep(0.2)
            pyautogui.click()
            time.sleep(0.5)  # 等待复制完成
            content = self.get_clipboard_content()
            self.log.log(f"{self.name} 通过按钮复制内容: [{content}]")
            return content
        except Exception as e:
            self.log.log(f"{self.name} 复制消息失败: {e}", "error")
            return "" 