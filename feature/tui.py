import npyscreen


msg = str()

class ACBForm(npyscreen.Form):
    def __init__(self, name=None, parentApp=None, framed=None, help=None, color='FORMDEFAULT', widget_list=None, cycle_widgets=False, *args, **keywords):
        """AutoConvoBridge的窗口
        
        """
        
        super().__init__(name, parentApp, framed, help, color, widget_list, cycle_widgets, *args, **keywords)
    
    def afterEditing(self):
        self.parentApp.setNextForm(None)
        
    def create(self):
        self.initialize_args()
        self.initialize_boxes()
        self.initialize_widgets()
        
    def initialize_args(self):
        SPACING = 1
        # MIN_SUPPORED_HALF_WIDTH = 40
        total_width = self.columns
        total_height = self.lines

        self.half_width = (total_width - SPACING - 2) // 2
        self.half_height = (total_height - SPACING - 2) // 2
#         print(total_width)
#         if self.half_width < MIN_SUPPORED_HALF_WIDTH:
#             npyscreen.notify_confirm(
#                 f"""终端宽度不足！\n
# 请拉宽终端\n
# 否则可能出现显示问题""",
#                 title="警告",
#                 wide=True
#             )

        self.lower_height = 7
        self.upper_height = total_height - self.lower_height - (SPACING * 2)
        self.upper_height = max(12, min(self.upper_height, 48))


        self.left_start_relx = 1
        self.right_start_relx = self.half_width + SPACING
        
        self.upper_start_rely = 2
        self.lower_start_rely = self.upper_start_rely + self.upper_height + SPACING
        self.lower_start_rely = min(self.lower_start_rely, total_height - self.lower_height - SPACING)
        
    def initialize_boxes(self):
        # need self.initialize_args be run
        self.wx_box = self.add(
            npyscreen.BoxTitle,
            name="WINDOW1 WX SETTING",
            relx=self.left_start_relx,
            rely=self.upper_start_rely,
            width=self.half_width,
            height=self.upper_height,
            editable = False
        )

        self.ai_box = self.add(
            npyscreen.BoxTitle,
            name="WINDOW2 AI SETTING",
            relx=self.right_start_relx,
            rely=self.upper_start_rely,
            width=self.half_width,
            height=self.upper_height,
            editable=False
        )
        self.save_load_box = self.add(
            npyscreen.BoxTitle,
            name="SETTINGS FROM FILE",
            relx=self.left_start_relx,
            rely=self.lower_start_rely,
            width=self.half_width,
            height=self.lower_height,
            editable=False
        )
        self.start_box = self.add(
            npyscreen.BoxTitle,
            name="RUN ACB",
            relx=self.right_start_relx,
            rely=self.lower_start_rely,
            width=self.half_width,
            height=self.lower_height,
            editable=False
        )


    def initialize_widgets(self):
        # ===== 微信组件：独立纵向坐标，确保正常显示+有序排列 =====
        wx_start_relx = self.left_start_relx + 2
        wx_current_rely = self.upper_start_rely + 2  # 初始化纵向坐标

        # 微信输入框坐标
        self.wx_send_coordinate_note = self.add(
            npyscreen.FixedText,
            value="wx_send_coordinate [x, y]",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=self.half_width - 6,
        )
        wx_current_rely += 1  # 换行

        self.wx_send_coordinate_x = self.add(
            npyscreen.TitleText,
            name="  - x:",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=20,
        )
        wx_current_rely += 1  # 换行

        self.wx_send_coordinate_y = self.add(
            npyscreen.TitleText,
            name="  - y:",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=20,
        )
        wx_current_rely += 3  

        # 微信来信坐标
        self.wx_reply_coordinate_note = self.add(
            npyscreen.FixedText,
            value="wx_reply_coordinate [x, y]",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=self.half_width - 6,
        )
        wx_current_rely += 1  # 换行

        self.wx_reply_coordinate_x = self.add(
            npyscreen.TitleText,
            name="  - x:",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=20,
        )
        wx_current_rely += 1  # 换行

        self.wx_reply_coordinate_y = self.add(
            npyscreen.TitleText,
            relx=wx_start_relx,
            name="  - y:",
            rely=wx_current_rely,
            max_width=20,
        )
        wx_current_rely += 3  

        # 微信来信监视区域
        self.wx_reply_window_note = self.add(
            npyscreen.FixedText,
            value="wx_reply_coordinate [[x1, y1], [x2, y2]]",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=self.half_width - 6,
        )
        wx_current_rely += 1  # 换行

        self.wx_reply_window_x1 = self.add(
            npyscreen.TitleText,
            name="  - x1:",
            max_width=20,
            relx=wx_start_relx,
            rely=wx_current_rely,
        )
        wx_current_rely += 1  # 换行

        self.wx_reply_window_y1 = self.add(
            npyscreen.TitleText,
            name="  - y1:",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=20,
        )
        wx_current_rely += 2  # 换行

        self.wx_reply_window_x2 = self.add(
            npyscreen.TitleText,
            name="  - x2:",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=20,
        )
        wx_current_rely += 1  # 换行

        self.wx_reply_window_y2 = self.add(
            npyscreen.TitleText,
            name="  - y2:",
            relx=wx_start_relx,
            rely=wx_current_rely,
            max_width=20,
        )
        wx_current_rely += 1  # 换行

        # ===== AI组件：独立纵向坐标，与微信组件无关联，确保操作便捷 =====
        ai_start_relx = self.right_start_relx + 2
        ai_current_rely = self.upper_start_rely + 2  # 独立初始化，不依赖微信坐标

        # AI输入框坐标
        self.ai_send_coordinate_note = self.add(
            npyscreen.FixedText,
            value="ai_send_coordinate [x, y]",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=self.half_width - 6,
        )
        ai_current_rely += 1  # 换行

        self.ai_send_coordinate_x = self.add(
            npyscreen.TitleText,
            name="  - x:",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=20,
        )
        ai_current_rely += 1  # 换行

        self.ai_send_coordinate_y = self.add(
            npyscreen.TitleText,
            name="  - y:",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=20,
        )
        ai_current_rely += 3

        # AI来信坐标
        self.ai_reply_coordinate_note = self.add(
            npyscreen.FixedText,
            value="ai_reply_coordinate [x, y]",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=self.half_width - 6,
        )
        ai_current_rely += 1  # 换行

        self.ai_reply_coordinate_x = self.add(
            npyscreen.TitleText,
            name="  - x:",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=20,
        )
        ai_current_rely += 1  # 换行

        self.ai_reply_coordinate_y = self.add(
            npyscreen.TitleText,
            relx=ai_start_relx,
            name="  - y:",
            rely=ai_current_rely,
            max_width=20,
        )
        ai_current_rely += 3

        # AI来信监视区域
        self.ai_reply_window_note = self.add(
            npyscreen.FixedText,
            value="ai_reply_coordinate [[x1, y1], [x2, y2]]",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=self.half_width - 6,
        )
        ai_current_rely += 1  # 换行

        self.ai_reply_window_x1 = self.add(
            npyscreen.TitleText,
            name="  - x1:",
            max_width=20,
            relx=ai_start_relx,
            rely=ai_current_rely,
        )
        ai_current_rely += 1  # 换行

        self.ai_reply_window_y1 = self.add(
            npyscreen.TitleText,
            name="  - y1:",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=20,
        )
        ai_current_rely += 2  # 换行

        self.ai_reply_window_x2 = self.add(
            npyscreen.TitleText,
            name="  - x2:",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=20,
        )
        ai_current_rely += 1  # 换行

        self.ai_reply_window_y2 = self.add(
            npyscreen.TitleText,
            name="  - y2:",
            relx=ai_start_relx,
            rely=ai_current_rely,
            max_width=20,
        )

        self.load_button = self.add(
            npyscreen.ButtonPress,
            name="Load setting",
            relx=wx_start_relx,
            rely=self.lower_start_rely + 2
        )

        self.save_button = self.add(
            npyscreen.ButtonPress,
            name="Save setting",
            relx=wx_start_relx,
            rely=self.lower_start_rely + 4
        )
        
        
        self.run_button = self.add(
            npyscreen.ButtonPress,
            name="RUN",
            relx=ai_start_relx,
            rely=self.lower_start_rely + 2
        )
        
        self.quit_button = self.add(
            QuitButtonPress,
            name="Quit",
            relx=ai_start_relx,
            rely=self.lower_start_rely + 4,
            # whenPressed = self.on_quit_press
        )

    def on_quit_press(self):
        self.editing = False
        self.parentApp.setNextForm(None)
        
        
class QuitButtonPress(npyscreen.ButtonPress):
    def whenPressed(self):
        self.parent.setNextForm(None)
        return super().whenPressed()
    
class ACBApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", ACBForm, name="AutoConvoBridge")
        
        return super().onStart()
    
class AutoConvoBridge:
    def __init__(self):

        self.app = ACBApp()
        self.app.run()
        
        mainform = self.app.getForm("MAIN")




AutoConvoBridge()