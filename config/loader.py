import logging
import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from models.config import ServerConfig, NginxConfig, ElasticsearchConfig, DatabaseConfig, GeoIpConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Config(BaseModel):
    server: ServerConfig
    nginx: NginxConfig
    elasticsearch: ElasticsearchConfig
    database: DatabaseConfig
    geoip: GeoIpConfig


def load_config(config_path: str) -> Config:
    if not os.path.exists(config_path):
        logging.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        config = Config(**data)
        config.database.url = __fix_url(config.database.url)
        config.server.static_path = __fix_url(config.server.static_path)
        config.geoip.data_path = __fix_url(config.geoip.data_path)
        return config
    except ValidationError as e:
        logging.error(f"Failed to validate config: {e}")
        raise
    except Exception as e:
        logging.error(f"Failed to load or validate config: {e}")
        raise RuntimeError(f"Failed to load or validate config: {e}") from e


def __fix_url(url: str) -> str:
    sqlite_prefix = "sqlite:///"
    project_prefix = "./"
    if url.startswith(sqlite_prefix) and not url.startswith("sqlite:////"):
        rel = url[len(sqlite_prefix):]
        return f"{sqlite_prefix}{(PROJECT_ROOT / rel).resolve().as_posix()}"
    if url.startswith(project_prefix):
        rel = url[len(project_prefix):]
        return f"{(PROJECT_ROOT / rel).resolve().as_posix()}"
    return url
