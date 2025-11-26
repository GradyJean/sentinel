# scheduler_test.py
import asyncio

from core.scheduler.scheduler import SchedulerManager


async def main():
    manager = SchedulerManager()
    manager.start()  # 现在会在事件循环内执行

    try:
        # 保持程序运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        manager.stop()


if __name__ == '__main__':
    asyncio.run(main())
