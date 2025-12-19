import config
from core.integrator.nginx import Nginx

nginx = Nginx(config.settings.nginx.root_path, config.CORE_OS)
