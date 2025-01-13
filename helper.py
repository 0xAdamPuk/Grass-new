import time
import subprocess

def run_script():
    while True:
        try:
            # 执行main2.py脚本
            subprocess.run(["python3", "main2.py"], check=True)
        except subprocess.CalledProcessError as e:
            # 捕获异常并打印错误信息
            print(f"Error occurred: {e}")
            print("Restarting the script in 5 seconds...")
            time.sleep(5)  # 等待 5 秒后重新执行脚本
        else:
            # 如果脚本正常退出，则跳出循环
            print("Script executed successfully.")
            break

if __name__ == "__main__":
    run_script()
