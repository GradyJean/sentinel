from core.integrator.nginx import Nginx
import config

nginx = Nginx(config.settings.nginx_base_path, config.CORE_OS)
