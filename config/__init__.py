from pathlib import Path
import os

from config.loader import load_config

# project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# settings
settings = load_config(f"{PROJECT_ROOT}/setting.yaml")
# core os
CORE_OS = "Unix"

if os.sep == '\\':
    CORE_OS = "Windows"
