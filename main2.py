import aiohttp
import asyncio
import base64
import datetime
import json
import random
import re
import ssl
import time
import uuid
import websockets

from loguru import logger
import pyfiglet
from websockets_proxy import Proxy, proxy_connect

logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=''),
    format=(
        "<green>{time:DD/MM/YY HH:mm:ss}</green> | "
        "<level>{level:8} | {message}</level>"
    ),
    colorize=True
)

# main.py
def print_header():
    cn = pyfiglet.figlet_format("小草脚本")
    print(cn)
    print("{╔═╗╔═╦╗─╔╦═══╦═══╦═══╦═══╗")
    print("{╚╗╚╝╔╣║─║║╔══╣╔═╗║╔═╗║╔═╗║")
    print("{─╚╗╔╝║║─║║╚══╣║─╚╣║─║║║─║║")
    print("{─╔╝╚╗║║─║║╔══╣║╔═╣╚═╝║║─║║")
    print("{╔╝╔╗╚╣╚═╝║╚══╣╚╩═║╔═╗║╚═╝║")
    print("{╚═╝╚═╩═══╩═══╩═══╩╝─╚╩═══╝")
    print("{我的gihub：github.com/Gzgod")
    print("{我的推特：推特雪糕战神@Hy78516012")

# 初始化头部信息
print_header()

def read_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def assign_proxies_to_uids(uid_file, proxy_file):
    uids = read_file(uid_file)
    proxies = read_file(proxy_file)

    # Check if proxies count is a positive integer multiple of uids count
    if len(proxies) % len(uids) != 0:
        raise ValueError("Number of proxies is not a positive integer multiple of the number of uids")

    N = len(proxies) // len(uids)
    uid_proxy_mapping = {}

    for i, uid in enumerate(uids):
        uid_proxy_mapping[uid] = proxies[i * N:(i + 1) * N]

    return uid_proxy_mapping, N

DELAY_INTERVAL = 0.5
MAX_RETRIES = 3
FILE_UID = "uid.txt"
FILE_PROXY = "proxy.txt"
USERAGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.57",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.52",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.46",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.128",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.112",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.98",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.83",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.133",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.121",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91"
]
HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

PROXY_ALLOCATION, ONETIME_PROXY = assign_proxies_to_uids(FILE_UID, FILE_PROXY)

print()
print(f"UID: {len(PROXY_ALLOCATION.keys())}. 来自 {FILE_UID}。")
print(f"加载了 {len(PROXY_ALLOCATION.keys())*ONETIME_PROXY} 个代理。来自 {FILE_PROXY}。")
print(f"每个任务激活的代理数量: {ONETIME_PROXY} 个代理。")
print()

# 获取用户输入以处理代理失败
def get_user_input():
    user_input = ""
    while user_input not in ['yes', 'no']:
        user_input = input("遇到特定失败时是否要移除代理 (yes/no)? ").strip().lower()
        if user_input not in ['yes', 'no']:
            print("无效输入。请输入 'yes' 或 'no'。")
    return user_input == 'yes'

remove_on_all_errors = get_user_input()
print(f"您选择了: {'是' if remove_on_all_errors else '否'}, ！\n")

# 默认使用 'extension' 节点类型
node_type = "extension"

def truncate_userid(user_id):
    return f"{user_id[:3]}--{user_id[-3:]}"

def truncate_proxy(proxy):
    pattern = r'([a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})|(?:\d{1,3}\.){3}\d{1,3})'
    match = re.search(pattern, proxy)
    if match:
        return match.group(0)
    return '未定义'

async def connect_to_wss(protocol_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, protocol_proxy))
    random_user_agent = random.choice(USERAGENTS)
    logger.info(f"UID: {truncate_userid(user_id)} | {node_type} | 生成设备ID: {device_id} | 代理: {truncate_proxy(protocol_proxy)}")

    has_received_action = False
    is_authenticated = False

    total_proxies = len(PROXY_ALLOCATION[user_id])
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi"
            }

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = [
                "wss://proxy2.wynd.network:4444", 
                "wss://proxy2.wynd.network:4650"
            ]
            uri = random.choice(urilist)
            server_hostname = uri.split("://")[1].split(":")[0]
            proxy = Proxy.from_url(protocol_proxy)

            async with proxy_connect(
                            uri,
                            proxy=proxy,
                            ssl=ssl_context,
                            server_hostname=server_hostname,
                            extra_headers=custom_headers
                        ) as websocket:
                logger.success(f"UID: {truncate_userid(user_id)} | {node_type} | 成功连接到WS | uri: {uri} | 头部信息: {custom_headers} | 设备ID: {device_id} | 代理: {truncate_proxy(protocol_proxy)} | 剩余代理数量: {total_proxies}")

                async def send_ping():
                    while True:
                        if has_received_action:
                            send_message = json.dumps({
                                "id": str(uuid.uuid4()),
                                "version": "1.0.0",
                                "action": "PING",
                                "data": {}
                            })
                            logger.debug(f"UID: {truncate_userid(user_id)} | {node_type} | 发送PING消息 | 数据: {send_message}")
                            await asyncio.sleep(DELAY_INTERVAL)
                            await websocket.send(send_message)
                            logger.info(f"UID: {truncate_userid(user_id)} | {node_type} | 已发送PING | 数据: {send_message}")

                        rand_sleep = random.uniform(10, 30)
                        logger.info(f"UID: {truncate_userid(user_id)} | {node_type} | 下次PING在 {rand_sleep:.2f} 秒后，！")
                        await asyncio.sleep(rand_sleep)

                await asyncio.sleep(DELAY_INTERVAL)
                send_ping_task = asyncio.create_task(send_ping())

                try:
                    while True:
                        if is_authenticated and not has_received_action:
                            logger.info(f"UID: {truncate_userid(user_id)} | {node_type} | 已认证 | 等待PING门开启以获取 HTTP请求")

                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(f"UID: {truncate_userid(user_id)} | {node_type} | 接收到消息 | 数据: {message}")

                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": random_user_agent,
                                    "timestamp": int(time.time()),
                                    "device_type": "extension",
                                    "version": "4.26.2",
                                    "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
                                }
                            }

                            logger.debug(f"UID: {truncate_userid(user_id)} | {node_type} | 发送AUTH | 数据: {auth_response}")
                            await asyncio.sleep(DELAY_INTERVAL)
                            await websocket.send(json.dumps(auth_response))
                            logger.success(f"UID: {truncate_userid(user_id)} | {truncate_proxy(protocol_proxy)} | {node_type} | 已发送AUTH | 数据: {auth_response}")
                            is_authenticated = True

                        elif message.get("action") in ["HTTP_REQUEST", "OPEN_TUNNEL"]:
                            has_received_action = True
                            request_data = message["data"]

                            headers = {
                                "User-Agent": custom_headers["User-Agent"],
                                "Content-Type": "application/json; charset=utf-8"
                            }

                            async with aiohttp.ClientSession() as session:
                                async with session.get(request_data["url"], headers=headers) as api_response:
                                    content = await api_response.text()
                                    encoded_body = base64.b64encode(content.encode()).decode()

                                    status_text = HTTP_STATUS_CODES.get(api_response.status, "")

                                    http_response = {
                                        "id": message["id"],
                                        "origin_action": message["action"],
                                        "result": {
                                            "url": request_data["url"],
                                            "status": api_response.status,
                                            "status_text": status_text,
                                            "headers": dict(api_response.headers),
                                            "body": encoded_body
                                        }
                                    }

                                    logger.info(f"UID: {truncate_userid(user_id)} | {node_type} | 打开PING访问 | 数据: {http_response}")
                                    await asyncio.sleep(DELAY_INTERVAL)
                                    await websocket.send(json.dumps(http_response))
                                    logger.success(f"UID: {truncate_userid(user_id)} | {truncate_proxy(protocol_proxy)} | {node_type} | 已发送PING访问 | 数据: {http_response}")

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(f"UID: {truncate_userid(user_id)} | {node_type} | 发送PONG | 数据: {pong_response}")
                            await asyncio.sleep(DELAY_INTERVAL)
                            await websocket.send(json.dumps(pong_response))
                            logger.success(f"UID: {truncate_userid(user_id)} | {truncate_proxy(protocol_proxy)} | {node_type} | 已发送PONG | 数据: {pong_response}")

                except websockets.exceptions.ConnectionClosedError as e:
                    logger.error(f"UID: {truncate_userid(user_id)} | {node_type} | 连接关闭错误 | 代理: {truncate_proxy(protocol_proxy)} | 错误: {str(e)} | 剩余代理数量: {total_proxies}")
                    await asyncio.sleep(DELAY_INTERVAL)
                finally:
                    await websocket.close()
                    logger.warning(f"UID: {truncate_userid(user_id)} | {node_type} | WebSocket连接已关闭 | 代理: {truncate_proxy(protocol_proxy)} | 剩余代理数量: {total_proxies}")
                    send_ping_task.cancel()
                    await asyncio.sleep(DELAY_INTERVAL)
                    break

        except Exception as e:
            logger.error(f"UID: {truncate_userid(user_id)} | {node_type} | 代理 {truncate_proxy(protocol_proxy)} 出现错误 ➜ {str(e)} | 剩余代理数量: {total_proxies}")
            error_conditions = [
                "403 Forbidden",
                "Host unreachable",
                "Empty host component",
                "Invalid scheme component",
                "[SSL: WRONG_VERSION_NUMBER]",
                "invalid length of packed IP address string",
                "Empty connect reply",
                "Device creation limit exceeded",
                "[Errno 111] Could not connect to proxy",
                "sent 1011 (internal error) keepalive ping timeout; no close frame received"
            ]
            skip_proxy = [
                "Proxy connection timed out: 60",
                "407 Proxy Authentication Required",
                "Invalid port component"
            ]

            if any(error_msg in str(e) for error_msg in skip_proxy):
                logger.warning(f"UID: {truncate_userid(user_id)} | {node_type} | 由于错误跳过代理 ➜ {truncate_proxy(protocol_proxy)} | 剩余代理数量: {total_proxies}")
                return "skip"

            if remove_on_all_errors:
                if any(error_msg in str(e) for error_msg in error_conditions):
                    logger.warning(f"UID: {truncate_userid(user_id)} | {node_type} | 由于错误移除代理 ➜ {truncate_proxy(protocol_proxy)} | 剩余代理数量: {total_proxies}")
                    remove_specific_proxy(PROXY_ALLOCATION, user_id, protocol_proxy)
                    return None
            else:
                if "Device creation limit exceeded" in str(e):
                    logger.warning(f"UID: {truncate_userid(user_id)} | {node_type} | 由于错误移除代理 ➜ {truncate_proxy(protocol_proxy)} | 剩余代理数量: {total_proxies}")
                    remove_specific_proxy(PROXY_ALLOCATION, user_id, protocol_proxy)
                    return None

            await asyncio.sleep(DELAY_INTERVAL)
            continue

# 创建一个全局的 asyncio.Lock 对象
lock = asyncio.Lock()

async def remove_specific_proxy(uid_proxy_mapping, uid, proxy):
    """
    Remove a specific proxy for the given uid in the uid_proxy_mapping dictionary.
    
    :param uid_proxy_mapping: dict, the dictionary containing uid-proxy mappings
    :param uid: str, the uid for which to remove the proxy
    :param proxy: str, the proxy to be removed
    :return: None
    """
    async with lock:
        if uid in uid_proxy_mapping:
            if proxy in uid_proxy_mapping[uid]:
                # Remove the specific proxy from the list
                uid_proxy_mapping[uid].remove(proxy)
                print(f"Proxy {proxy} removed from uid: {uid}")
            else:
                print(f"Proxy {proxy} not found for uid: {uid}")
        else:
            print(f"uid: {uid} not found in uid_proxy_mapping")

async def main():
    retry_count = {}

    for user_id, proxies in PROXY_ALLOCATION.items():
        logger.warning(f"UID: {truncate_userid(user_id)} | {node_type} | 使用的代理总数: {len(proxies)}")
        await asyncio.sleep(DELAY_INTERVAL)

    tasks = {}

    for user_id, proxies in PROXY_ALLOCATION.items():
        for proxy in proxies:
            retry_count[(proxy, user_id)] = 0
            await asyncio.sleep(DELAY_INTERVAL)
            task = asyncio.create_task(connect_to_wss(proxy, user_id))
            tasks[task] = (proxy, user_id)

    while True:
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            try:
                result = task.result()

                failed_proxy, user_id = tasks[task]

                if result == "skip":
                    retry_count[(failed_proxy, user_id)] += 1

                    if retry_count[(failed_proxy, user_id)] > MAX_RETRIES:
                        remove_specific_proxy(PROXY_ALLOCATION, user_id, failed_proxy)
                        logger.warning(f"UID: {truncate_userid(user_id)} | {node_type} | 达到最大重试次数（跳过代理）: {truncate_proxy(failed_proxy)}。")
                        continue

                    await asyncio.sleep(DELAY_INTERVAL)
                    new_task = asyncio.create_task(connect_to_wss(failed_proxy, user_id))
                    tasks[new_task] = (failed_proxy, user_id)
                    
                elif result is None:
                    retry_count[(failed_proxy, user_id)] += 1

                    if retry_count[(failed_proxy, user_id)] > MAX_RETRIES:
                        remove_specific_proxy(PROXY_ALLOCATION, user_id, failed_proxy)
                        logger.warning(f"UID: {truncate_userid(user_id)} | {node_type} | 达到最大重试次数（跳过代理）: {truncate_proxy(failed_proxy)}。")
                        continue

            except Exception as e:
                logger.error(f"UID: {truncate_userid(user_id)} | {node_type} | 处理任务时发生错误: {str(e)}")
            finally:
                tasks.pop(task)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info(f"用户终止程序。\n")
