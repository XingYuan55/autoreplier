import npyscreen

# 这里应用充当了 curses 初始化封装器的角色
# 同时也管理着应用的实际形态.

class MyTestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())

# 这个窗口类定义了展示给用户的显示内容.

class MainForm(npyscreen.Form):
    def create(self):
        
        self.add(npyscreen.TitleText, name = "Text:", value= "This is a text" )

    def afterEditing(self):
        self.parentApp.setNextForm(None)

if __name__ == '__main__':
    TA = MyTestApp()
    TA.run()