import os
import logging
from models.config import ServerConfig, NginxConfig, ElasticsearchConfig
import yaml
from pydantic import BaseModel, ValidationError


class Config(BaseModel):
    server: ServerConfig
    nginx: NginxConfig
    elasticsearch: ElasticsearchConfig


def load_config(config_path: str) -> Config:
    if not os.path.exists(config_path):
        logging.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        config = Config(**data)
        return config
    except Exception as e:
        logging.error(f"Failed to load or validate config: {e}")
        raise ValidationError(f"Failed to load or validate config: {e}")
