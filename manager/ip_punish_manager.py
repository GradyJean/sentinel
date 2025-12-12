from models.punish import PunishLevel, PunishRecord
from storage.document import ElasticSearchRepository


class PunishLevelManager(ElasticSearchRepository[PunishLevel]):
    """
    处罚等级服务
    """

    def __init__(self):
        super().__init__("punish_level", PunishLevel)


class PunishRecordManager(ElasticSearchRepository[PunishRecord]):
    """
    处罚记录服务
    """

    def __init__(self):
        super().__init__("punish_record", PunishRecord)
