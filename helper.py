import subprocess
import psutil
import time

def run_script():
    while True:
        # 启动 main2.py 并获取进程对象
        process = subprocess.Popen(["python3", "main2.py"])
        pid = process.pid
        print(f"Started main2.py with PID: {pid}")

        # 将 PID 保存到 pid.txt 文件中
        with open("pid.txt", "w") as f:
            f.write(str(pid))

        # 监控进程状态
        while True:
            try:
                # 检查进程是否存在
                p = psutil.Process(pid)
                # p.status() 可以用来检查进程的状态
                if p.status() == psutil.STATUS_ZOMBIE:
                    raise psutil.NoSuchProcess(pid)
            except psutil.NoSuchProcess:
                # 如果进程不存在或状态为僵尸进程，则重新启动
                print(f"Process {pid} terminated. Restarting in 5 seconds...")
                time.sleep(5)
                break
            except Exception as e:
                print(f"Error occurred while monitoring process {pid}: {e}")
                time.sleep(5)
                break

            # 等待一段时间后继续检查
            time.sleep(1)

if __name__ == "__main__":
    run_script()
