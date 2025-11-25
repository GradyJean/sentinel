from typing import Optional

from pydantic import BaseModel, Field


class ElasticsearchModel(BaseModel):
    id: Optional[str] = Field(default=None, exclude=True)  # 可选的ID字段，序列化时排除
