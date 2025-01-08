# 小草脚本 1.25倍率

## 教程

1. 安装所需环境
   ```bash
   sudo apt update -y && apt install -y python3 python3-venv pip
   ```

2. 安装库并运行脚本
   ```bash
   git clone https://github.com/0xAdamPuk/Grass-new && cd Grass-new
   python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   python3 main2.py
   ```

## ID获取
- 如果您还没有注册，可以使用我的链接： ([点击注册](https://app.getgrass.io/register?referralCode=DzRrYsxB0uj0gIY)).
- 如何获取您的用户ID？
  - 登录并打开 https://app.getgrass.io/dashboard
  - 在浏览器中打开开发人员工具 (F12) / 检查元素。
  - 在“控制台（console）”选项卡中，输入：
   `localStorage.getItem('userId');`
  - 复制不带“”或“”的结果并将其粘贴到“uid.txt”中。
  - 对于多个帐户，将每个 uid 添加到新行，例如：
       ```
     uid1
     uid2
     uid2
     ```

## 代理格式 按照以下格式填写proxy.txt
 ```bash
http://user:password@ip:port
   ```



## 运行成功后，失败的代理会如图红色部分所示，成功的代理会如图绿色所示
![1](https://github.com/user-attachments/assets/a1d8356d-94cc-4566-bc7b-0d016c093666)

