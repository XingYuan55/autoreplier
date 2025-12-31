import npyscreen


msg = str()

class ACBForm(npyscreen.Form):
    def afterEditing(self):
        self.parentApp.setNextForm(None)
        
    def create(self):
        self.add(npyscreen.FixedText, name="Coordinate of Window 1 AI")
        ...
        #TODO
        
    def initialize_double_column(self):
        total_width = self.columns
        min_supported_width = 50
        
        if total_width < min_supported_width:
            npyscreen.notify_confirm(
                f"""终端宽度不足！
最小需要： {min_supported_width} 格字符宽
当前：{total_width} 格字符宽
请拉宽终端，否则将强制使用最小宽度计算，可能出现显示问题"""
            title="警告"
            )
            
            total_width = min_supported_width
            
        LEFT_COL_RATIO = RIGHT_COL_RATIO = 0.45
        SPACING_RATIO = 1 - LEFT_COL_RATIO - RIGHT_COL_RATIO
        
        left_col_width = int(total_width * LEFT_COL_RATIO)
        right_col_width = int(total_width * RIGHT_COL_RATIO)
        self = 
            
            
        
    
class ACBApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", ACBForm, name="AutoConvoBridge")
        
        return super().onStart()
    
class AutoConvoBridge:
    def __init__(self):

        self.app = ACBApp()
        self.app.run()
        
        mainform = self.app.getForm("MAIN")
        print(mainform.text.value)
        
AutoConvoBridge()