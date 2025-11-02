import logging
import os
import subprocess


class Nginx:
    """
    nginx 操作类
    """

    def __init__(self, nginx_path: str, core_os: str = "Unix"):
        self.nginx_path = self.__get_nginx_path(nginx_path, core_os)

    @staticmethod
    def __get_nginx_path(nginx_path: str, core_os: str) -> str:
        """
        获取 nginx 路径
        """
        nginx_bin = None
        bin_name = "nginx"
        if core_os == "windows":
            bin_name = "nginx.exe"

        # 检查常见路径
        possible_paths = [
            f"{nginx_path}/sbin/{bin_name}",
            f"/usr/local/nginx/sbin/{bin_name}",
            f"/opt/nginx/sbin/{bin_name}"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                nginx_bin = path
                break
        if not nginx_bin:
            raise FileNotFoundError("Nginx not found")
        return nginx_bin

    def test(self) -> bool:
        """
        测试 nginx 配置
        """
        try:
            result = subprocess.run([self.nginx_path, "-t"], capture_output=True, text=True)
            logging.info(result.stdout)
            logging.info(result.stderr)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error testing nginx config: {e}")
            return False

    def reload(self) -> bool:
        """
        重载 nginx
        """
        try:
            result = subprocess.run([self.nginx_path, "-s", "reload"], capture_output=True, text=True)
            logging.info(result.stdout)
            logging.info(result.stderr)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error reloading nginx: {e}")
            return False

    def stop(self) -> bool:
        """
        停止 nginx
        """
        try:
            result = subprocess.run([self.nginx_path, "-s", "stop"], capture_output=True, text=True)
            logging.info(result.stdout)
            logging.info(result.stderr)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error stopping nginx: {e}")
            return False

    def start(self) -> bool:
        """
        启动 nginx
        """
        try:
            result = subprocess.run([self.nginx_path], capture_output=True, text=True)
            logging.info(result.stdout)
            logging.info(result.stderr)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error starting nginx: {e}")
            return False
