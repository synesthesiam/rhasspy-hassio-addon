"""Settings for Rhasspy."""
import logging
import os
from typing import Any, Dict, List

import json5
import pydash

from rhasspy.utils import recursive_update

# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)


class Profile:
    """Contains all settings for Rhasspy."""

    def __init__(
        self,
        name: str,
        system_profiles_dir: str,
        user_profiles_dir: str,
        layers: str = "all",
    ) -> None:

        self.name: str = name
        self.system_profiles_dir = system_profiles_dir
        self.user_profiles_dir = user_profiles_dir
        self.profiles_dirs: List[str] = [user_profiles_dir, system_profiles_dir]
        self.layers: str = layers
        self.load_profile()

    # -------------------------------------------------------------------------

    @classmethod
    def load_defaults(cls, system_profiles_dir: str) -> Dict[str, Any]:
        """Load default profile settings."""
        defaults_path = os.path.join(system_profiles_dir, "defaults.json")
        with open(defaults_path, "r") as defaults_file:
            logging.debug("Loading default profile settings from %s", defaults_path)
            return json5.load(defaults_file)

    # -------------------------------------------------------------------------

    def get(self, path: str, default: Any = None) -> Any:
        """Get setting by path."""
        return pydash.get(self.json, path, default)

    def set(self, path: str, value: Any) -> None:
        """Set setting by path."""
        pydash.set_(self.json, path, value)

    # -------------------------------------------------------------------------

    def load_profile(self) -> None:
        """Load defaults and user settings."""
        # Load defaults first
        self.json: Dict[str, Any] = {}  # no defaults
        self.system_json: Dict[str, Any] = {}  # no defaults

        if self.layers in ["all", "defaults"]:
            defaults_path = os.path.join(self.system_profiles_dir, "defaults.json")
            with open(defaults_path, "r") as defaults_file:
                self.json = json5.load(defaults_file)
                defaults_file.seek(0)
                self.system_json = json5.load(defaults_file)

        # Load just the system profile.json (on top of defaults)
        system_profile_path = os.path.join(
            self.system_profiles_dir, self.name, "profile.json"
        )

        with open(system_profile_path, "r") as system_profile_file:
            recursive_update(self.system_json, json5.load(system_profile_file))

        # Overlay with profile
        self.json_path = self.read_path("profile.json")
        if self.layers in ["all", "profile"]:
            # Read in reverse order so user profile overrides system
            for profiles_dir in self.profiles_dirs[::-1]:
                json_path = os.path.join(profiles_dir, self.name, "profile.json")
                if os.path.exists(json_path):
                    with open(json_path, "r") as profile_file:
                        recursive_update(self.json, json5.load(profile_file))

    def read_path(self, *path_parts: str) -> str:
        """Get first readable path in user then system directories."""
        for profiles_dir in self.profiles_dirs:
            # Try to find in the user profile first
            full_path = os.path.join(profiles_dir, self.name, *path_parts)

            if os.path.exists(full_path):
                return full_path

        # Use base dir
        return os.path.join("profiles", self.name, path_parts[-1])

    def read_paths(self, *path_parts: str) -> List[str]:
        """Get all readable paths in user then system directories."""
        return_paths: List[str] = []

        for profiles_dir in self.profiles_dirs:
            # Try to find in the runtime profile first
            full_path = os.path.join(profiles_dir, self.name, *path_parts)

            if os.path.exists(full_path):
                return_paths.append(full_path)

        return return_paths

    def write_path(self, *path_parts: str) -> str:
        """Get first writeable path in user then system directories."""
        # Try to find in the runtime profile first
        for profiles_dir in self.profiles_dirs:
            full_path = os.path.join(profiles_dir, self.name, *path_parts)

            try:
                dir_path = os.path.split(full_path)[0]
                os.makedirs(dir_path, exist_ok=True)
                return full_path
            except Exception:
                logger.exception("Unable to write to %s", full_path)

        # Use base dir
        full_path = os.path.join("profiles", self.name, *path_parts)
        dir_path = os.path.split(full_path)[0]
        os.makedirs(dir_path, exist_ok=True)

        return full_path

    def write_dir(self, *dir_parts: str) -> str:
        """Get first writeable directory in user then system directories."""
        # Try to find in the runtime profile first
        for profiles_dir in self.profiles_dirs:
            dir_path = os.path.join(profiles_dir, self.name, *dir_parts)

            try:
                os.makedirs(dir_path, exist_ok=True)
                return dir_path
            except Exception:
                logger.exception("Unable to create %s", dir_path)

        # Use base dir
        dir_path = os.path.join("profiles", self.name, *dir_parts)
        os.makedirs(dir_path, exist_ok=True)

        return dir_path
