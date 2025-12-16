from typing import Dict, Any

from loguru import logger

from models.config import SystemConfig
from storage.document import ElasticSearchRepository


class SystemConfigManager(ElasticSearchRepository[SystemConfig]):
    """
    任务调度服务
    """
    system_config: Dict[str, Any]

    def __init__(self):
        super().__init__("system_config", SystemConfig)

    def load_config(self):
        """
        加载系统配置
        """
        system_configs = self.get_all()
        if not system_configs:
            logger.warning("system config is empty")
        self.system_config = {config.key: config.value for config in system_configs}
