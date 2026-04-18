# /src/core/update_manager.py
import requests
import subprocess
import os
import sys
import hashlib
import logging
from packaging.version import parse
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class UpdateManager:
    """
    Manages application updates by checking a remote version manifest.
    """
    def __init__(self, config_manager: ConfigManager):
        """
        Initializes the UpdateManager.
        Args:
            config_manager (ConfigManager): An instance of ConfigManager.
        """
        self.config = config_manager
        self.current_version = self.config.get_setting('app_info.version', '0.0.0')
        self.updater_url = self.config.get_setting('updater.url')
        self.updater_enabled = self.config.get_setting('updater.enabled', False)

    def _get_remote_version_info(self):
        """Fetches the remote version manifest."""
        if not self.updater_url:
            logger.warning("Updater URL is not configured.")
            return None
        try:
            response = requests.get(self.updater_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch remote version info: {e}")
            return None

    def _verify_checksum(self, file_path, expected_hash):
        """Verifies the SHA-256 checksum of a file."""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == expected_hash
        except FileNotFoundError:
            logger.error(f"Downloaded file not found at {file_path} for checksum.")
            return False

    def check_for_updates(self):
        """
        Checks for updates and initiates download and installation if a new version is found.
        """
        if not self.updater_enabled:
            logger.info("Updater is disabled in config.")
            return

        logger.info(f"Current version: {self.current_version}. Checking for updates...")
        
        remote_info = self._get_remote_version_info()
        if not remote_info:
            return

        latest_version = remote_info.get('version')
        installer_url = remote_info.get('url')
        expected_hash = remote_info.get('sha256')

        if not all([latest_version, installer_url, expected_hash]):
            logger.error("Remote version manifest is incomplete.")
            return

        if parse(latest_version) > parse(self.current_version):
            logger.info(f"New version found: {latest_version}. Downloading...")
            self._download_and_install(installer_url, expected_hash)
        else:
            logger.info("Application is up to date.")

    def _download_and_install(self, url, expected_hash):
        """Downloads and installs the update."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            installer_name = os.path.basename(url)
            installer_path = os.path.join(os.path.expanduser("~"), "Downloads", installer_name)

            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded installer to {installer_path}")

            if self._verify_checksum(installer_path, expected_hash):
                logger.info("Checksum verified. Starting installer...")
                # Note: This is for Windows .msi installers. Adapt for other OS/installer types.
                subprocess.Popen(["msiexec", "/i", installer_path, "/quiet"])
                sys.exit() # Exit the current application
            else:
                logger.error("Checksum verification failed! The downloaded file may be corrupt or tampered with. Deleting.")
                os.remove(installer_path)

        except requests.RequestException as e:
            logger.error(f"Failed to download update: {e}")
        except Exception as e:
            logger.error(f"An error occurred during the update process: {e}")

