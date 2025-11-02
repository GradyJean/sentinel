import os
import json
import time
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class SamplingState:
    """记录采样状态快照"""
    timestamp: float
    file_size: int
    offset: int
    avg_ratio: float
    interval: int
    duration: int
    system_state: str


class AdaptiveController:
    """
    Sentinel 自适应采样控制器
    根据日志增长速率与采样速率自动调整 interval 与 duration
    """

    def __init__(
            self,
            state_file: str = "/tmp/sentinel_adaptive_state.json",
            init_interval: int = 600,
            init_duration: int = 600,
            alpha: float = 0.3,
            min_interval: int = 60,
            max_interval: int = 1800,
    ):
        self.state_file = state_file
        self.alpha = alpha
        self.min_interval = min_interval
        self.max_interval = max_interval

        # 初始化状态
        self.state = SamplingState(
            timestamp=time.time(),
            file_size=0,
            offset=0,
            avg_ratio=1.0,
            interval=init_interval,
            duration=init_duration,
            system_state="BALANCED",
        )

        self._load_state()

    # ---------------------------
    # 持久化与状态管理
    # ---------------------------
    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.state = SamplingState(**data)
                    logger.info(f"加载上次控制器状态: {data}")
            except Exception as e:
                logger.warning(f"无法加载状态文件: {e}")

    def _save_state(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(asdict(self.state), f, indent=2)
        except Exception as e:
            logger.error(f"保存控制器状态失败: {e}")

    # ---------------------------
    # 主算法逻辑
    # ---------------------------
    def adjust(self, file_size_now: int, offset_now: int):
        """
        根据当前文件大小与偏移量调整采样频率
        :param file_size_now: 当前日志文件大小（最大偏移量）
        :param offset_now: 当前采样完成的偏移量
        :return: (new_interval, new_duration)
        """
        now = time.time()
        Δt = now - self.state.timestamp or 1
        Δfile = max(file_size_now - self.state.file_size, 0)
        Δoffset = max(offset_now - self.state.offset, 1)

        write_rate = Δfile / Δt
        read_rate = Δoffset / Δt
        ratio = write_rate / max(read_rate, 1e-6)

        # 平滑平均
        avg_ratio = self.alpha * ratio + (1 - self.alpha) * self.state.avg_ratio

        # ---------------------------
        # 决策逻辑
        # ---------------------------
        interval = self.state.interval
        duration = self.state.duration
        system_state = "BALANCED"

        if avg_ratio < 0.7:
            interval *= 1.2
            system_state = "IDLE"
        elif 0.7 <= avg_ratio <= 1.3:
            system_state = "BALANCED"
        elif 1.3 < avg_ratio <= 2.0:
            interval *= 0.8
            duration *= 1.2
            system_state = "OVERLOAD"
        else:  # > 2.0
            interval = max(interval * 0.5, self.min_interval)
            duration *= 1.5
            system_state = "BACKLOG"

        # 限制上下限
        interval = int(max(self.min_interval, min(interval, self.max_interval)))
        duration = int(max(60, min(duration, 3600)))

        # 更新状态
        self.state = SamplingState(
            timestamp=now,
            file_size=file_size_now,
            offset=offset_now,
            avg_ratio=avg_ratio,
            interval=interval,
            duration=duration,
            system_state=system_state,
        )

        self._save_state()

        logger.info(
            f"控制器更新 -> 状态={system_state}, ratio={avg_ratio:.2f}, "
            f"interval={interval}s, duration={duration}s, "
            f"write_rate={write_rate:.1f}B/s, read_rate={read_rate:.1f}B/s"
        )

        return interval, duration, system_state
