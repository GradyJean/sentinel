import random
import requests
import time  # 改为导入 time 模块

hots = "http://127.0.0.1:8081"
pages = [
    "/test1.html",
    "/test2.html",
    "/test3.html",
    "/test4.html",
    "/test5.html",
    "/test6.html",
    "/test7.html",
    "/test8.html",
    "/test9.html",
    "/test10.html",
]
count = 0
while True:
    result = None
    try:
        result = requests.get(hots + random.choice(pages))
        count += 1
    except Exception as e:
        continue
    finally:
        time.sleep(1)  # 使用 time.sleep()
        if result:
            print(f"{count} {result.status_code}")
