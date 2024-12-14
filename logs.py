import time
import signal

class logging:
    def __init__(self, file="logs.txt"):
        self.log_file = file
        self.begin_time = time.time()
        self.log_f = open(self.log_file, "a", encoding="utf-8")
        self.log(f"=== {time.strftime(r'%Y-%m-%d %H:%M:%S', time.localtime())} ===", "key")
        signal.signal(signal.SIGINT, self.handle_exit)

    def log(self, message, level="info"):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{int((time.time() - self.begin_time) * 10)}] - {level.upper()}: {message}\n")
            print(message)
            
    def handle_exit(self, signum, frame):
        """处理退出信号"""
        self.log("日志已保存", "key")
        print("\n日志已保存")
        self.log_f.close()
        exit(0)
            
    def __del__(self):
        if hasattr(self, 'log_f') and not self.log_f.closed:
            self.log_f.close()
    
if __name__ == "__main__":
    log = logging()
    while True:
        log.log("test")
        time.sleep(0.05)