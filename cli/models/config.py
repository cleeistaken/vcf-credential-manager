"""
VCF Configuration Model
Handles YAML configuration loading
"""

import yaml
from pathlib import Path
from typing import Optional
from .credential import Credential


class VcfConfig:
    """VCF Configuration from YAML"""
    
    def __init__(
        self,
        installer: Optional[Credential] = None,
        manager: Optional[Credential] = None
    ):
        self.installer = installer
        self.manager = manager
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> 'VcfConfig':
        """Load configuration from YAML file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        if not config_path.is_file():
            raise ValueError(f"Path is not a file: {config_path}")
        
        with open(config_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {config_path}: {e}")
        
        if not data:
            raise ValueError(f"Empty configuration file: {config_path}")
        
        installer = None
        if 'sddc_installer' in data:
            installer = Credential.from_dict(data['sddc_installer'])
        
        manager = None
        if 'sddc_manager' in data:
            manager = Credential.from_dict(data['sddc_manager'])
        
        if not installer and not manager:
            raise ValueError(
                "Configuration must contain at least 'sddc_installer' or 'sddc_manager'"
            )
        
        return cls(installer=installer, manager=manager)
    
    def __repr__(self) -> str:
        return (
            f"VcfConfig(installer={self.installer is not None}, "
            f"manager={self.manager is not None})"
        )
    
    @property
    def installer(self) -> Optional[Credential]:
        return self._installer
    
    @installer.setter
    def installer(self, value: Optional[Credential]) -> None:
        if value is not None and not isinstance(value, Credential):
            raise TypeError("installer must be a Credential instance")
        self._installer = value
    
    @property
    def manager(self) -> Optional[Credential]:
        return self._manager
    
    @manager.setter
    def manager(self, value: Optional[Credential]) -> None:
        if value is not None and not isinstance(value, Credential):
            raise TypeError("manager must be a Credential instance")
        self._manager = value

