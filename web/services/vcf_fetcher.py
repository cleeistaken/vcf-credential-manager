"""
VCF Credential Fetcher
Handles fetching credentials from VCF Installer and SDDC Manager
"""

import requests
import urllib3
import logging
from typing import List, Dict

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class VCFCredentialFetcher:
    """Fetches credentials from VCF Installer and SDDC Manager"""
    
    def __init__(self):
        self.session = requests.Session()
        # Set timeout for all requests
        self.timeout = 30
    
    def _get_token(self, host: str, username: str, password: str, ssl_verify: bool = False) -> str:
        """Get authentication token"""
        url = f"https://{host}/v1/tokens"
        headers = {"Content-Type": "application/json"}
        payload = {
            "username": username,
            "password": password,
        }
        
        logger.debug(f"Requesting token from {url} (SSL verify: {ssl_verify})")
        
        try:
            response = self.session.post(
                url, 
                json=payload, 
                headers=headers, 
                verify=ssl_verify,
                timeout=self.timeout
            )
            response.raise_for_status()
            token = response.json().get("accessToken")
            logger.debug(f"Successfully obtained token from {host}")
            return token
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error connecting to {host} - try disabling SSL verification")
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Connection timed out to {host}")
            raise
        except requests.exceptions.ConnectionError as e:
            # Extract useful info from connection error
            error_str = str(e)
            if "Connection refused" in error_str:
                logger.error(f"Connection refused to {host} - server may be down")
            elif "Name or service not known" in error_str or "getaddrinfo failed" in error_str:
                logger.error(f"Host not found: {host} - check hostname")
            else:
                logger.error(f"Connection failed to {host} - check network connectivity")
            raise
        except requests.exceptions.HTTPError as e:
            response = getattr(e, 'response', None)
            if response is not None and response.status_code == 401:
                logger.error(f"Authentication failed for {host} - check credentials")
            else:
                logger.error(f"HTTP error from {host}: {response.status_code if response else 'unknown'}")
            raise
        except Exception as e:
            logger.error(f"Error getting token from {host}: {type(e).__name__}")
            raise
    
    def fetch_from_installer(self, host: str, username: str, password: str, ssl_verify: bool = False) -> List[Dict]:
        """Fetch credentials from VCF Installer"""
        credentials = []
        
        try:
            # Get token
            token = self._get_token(host, username, password, ssl_verify)
            
            # Get SDDCs
            url = f"https://{host}/v1/sddcs"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = self.session.get(url, headers=headers, verify=ssl_verify, timeout=self.timeout)
            response.raise_for_status()
            sddcs = response.json().get("elements", [])
            
            logger.debug(f"Found {len(sddcs)} SDDCs from installer {host}")
            
            # Get credentials for each SDDC
            for sddc in sddcs:
                sddc_id = sddc.get("id")
                sddc_name = sddc.get("name", sddc_id)
                
                if sddc_id:
                    try:
                        spec_url = f"https://{host}/v1/sddcs/{sddc_id}/spec"
                        spec_response = self.session.get(spec_url, headers=headers, verify=ssl_verify, timeout=self.timeout)
                        spec_response.raise_for_status()
                        spec_data = spec_response.json()
                        
                        logger.debug(f"Parsing spec for SDDC: {sddc_name}")
                        
                        # Parse credentials from spec
                        creds = self._parse_installer_spec(spec_data)
                        credentials.extend(creds)
                        
                        logger.debug(f"Extracted {len(creds)} credentials from SDDC: {sddc_name}")
                        
                    except Exception as e:
                        logger.error(f"Error parsing SDDC {sddc_name}: {e}", exc_info=True)
                        # Continue with other SDDCs
                        continue
            
            return credentials
            
        except Exception as e:
            # Don't log full traceback for expected connection errors
            if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError, 
                            requests.exceptions.SSLError, requests.exceptions.HTTPError)):
                raise  # Already logged in _get_token
            logger.error(f"Error fetching from installer {host}: {type(e).__name__}: {str(e)[:100]}")
            raise
    
    def _parse_installer_spec(self, spec_data: Dict) -> List[Dict]:
        """Parse credentials from installer spec data"""
        credentials = []
        
        try:
            # Parse ESXi host credentials
            if 'hostSpecs' in spec_data:
                for host in spec_data['hostSpecs']:
                    try:
                        hostname = host.get('hostname', host.get('ipAddress', ''))
                        
                        # Credentials is a dictionary object (not a list)
                        if 'credentials' in host and isinstance(host['credentials'], dict):
                            creds_data = host['credentials']
                            credentials.append({
                                'hostname': hostname,
                                'username': creds_data.get('username', ''),
                                'password': creds_data.get('password', ''),
                                'credentialType': 'SSH',
                                'accountType': 'USER',
                                'resourceType': 'ESXI',
                                'source': 'VCF_INSTALLER'
                            })
                    except Exception as e:
                        logger.error(f"Error parsing ESXi host credentials for {hostname}: {e}", exc_info=True)
                        continue
            
            # Parse vCenter credentials
            if 'vcenterSpec' in spec_data:
                try:
                    vcenter = spec_data['vcenterSpec']
                    hostname = vcenter.get('vcenterHostname', vcenter.get('hostname', ''))
                    sso_domain = vcenter.get('ssoDomain', 'vsphere.local')
                    
                    # Root password
                    if 'rootVcenterPassword' in vcenter:
                        credentials.append({
                            'hostname': hostname,
                            'username': 'root',
                            'password': vcenter['rootVcenterPassword'],
                            'credentialType': 'SSH',
                            'accountType': 'USER',
                            'resourceType': 'VCENTER',
                            'source': 'VCF_INSTALLER'
                        })
                    
                    # SSO Admin password
                    if 'adminUserSsoPassword' in vcenter:
                        admin_user = f"administrator@{sso_domain}"
                        credentials.append({
                            'hostname': hostname,
                            'username': admin_user,
                            'password': vcenter['adminUserSsoPassword'],
                            'credentialType': 'SSO',
                            'accountType': 'SERVICE',
                            'resourceType': 'VCENTER',
                            'source': 'VCF_INSTALLER'
                        })
                except Exception as e:
                    logger.error(f"Error parsing vCenter credentials: {e}", exc_info=True)
            
            # Parse NSX-T credentials
            if 'nsxtSpec' in spec_data:
                try:
                    nsxt = spec_data['nsxtSpec']
                    vip_fqdn = nsxt.get('vipFqdn', '')
                    
                    # NSX Manager nodes
                    if 'nsxtManagers' in nsxt:
                        for manager in nsxt['nsxtManagers']:
                            try:
                                hostname = manager.get('hostname', manager.get('name', ''))
                                
                                # Root password (shared across all managers)
                                if 'rootNsxtManagerPassword' in nsxt:
                                    credentials.append({
                                        'hostname': hostname,
                                        'username': 'root',
                                        'password': nsxt['rootNsxtManagerPassword'],
                                        'credentialType': 'SSH',
                                        'accountType': 'USER',
                                        'resourceType': 'NSX_MANAGER',
                                        'source': 'VCF_INSTALLER'
                                    })
                                
                                # Admin password (shared across all managers)
                                if 'nsxtAdminPassword' in nsxt:
                                    credentials.append({
                                        'hostname': hostname,
                                        'username': 'admin',
                                        'password': nsxt['nsxtAdminPassword'],
                                        'credentialType': 'API',
                                        'accountType': 'SERVICE',
                                        'resourceType': 'NSX_MANAGER',
                                        'source': 'VCF_INSTALLER'
                                    })
                                
                                # Audit password (shared across all managers)
                                if 'nsxtAuditPassword' in nsxt:
                                    credentials.append({
                                        'hostname': hostname,
                                        'username': 'audit',
                                        'password': nsxt['nsxtAuditPassword'],
                                        'credentialType': 'API',
                                        'accountType': 'SERVICE',
                                        'resourceType': 'NSX_MANAGER',
                                        'source': 'VCF_INSTALLER'
                                    })
                            except Exception as e:
                                logger.error(f"Error parsing NSX manager credentials for {hostname}: {e}", exc_info=True)
                                continue
                    
                    # Also add VIP credentials if available
                    if vip_fqdn:
                        if 'rootNsxtManagerPassword' in nsxt:
                            credentials.append({
                                'hostname': vip_fqdn,
                                'username': 'root',
                                'password': nsxt['rootNsxtManagerPassword'],
                                'credentialType': 'SSH',
                                'accountType': 'USER',
                                'resourceType': 'NSX_VIP',
                                'source': 'VCF_INSTALLER'
                            })
                        
                        if 'nsxtAdminPassword' in nsxt:
                            credentials.append({
                                'hostname': vip_fqdn,
                                'username': 'admin',
                                'password': nsxt['nsxtAdminPassword'],
                                'credentialType': 'API',
                                'accountType': 'SERVICE',
                                'resourceType': 'NSX_VIP',
                                'source': 'VCF_INSTALLER'
                            })
                        
                        if 'nsxtAuditPassword' in nsxt:
                            credentials.append({
                                'hostname': vip_fqdn,
                                'username': 'audit',
                                'password': nsxt['nsxtAuditPassword'],
                                'credentialType': 'API',
                                'accountType': 'SERVICE',
                                'resourceType': 'NSX_VIP',
                                'source': 'VCF_INSTALLER'
                            })
                except Exception as e:
                    logger.error(f"Error parsing NSX-T credentials: {e}", exc_info=True)
            
            # Parse SDDC Manager credentials
            if 'sddcManagerSpec' in spec_data:
                try:
                    manager = spec_data['sddcManagerSpec']
                    hostname = manager.get('hostname', '')
                    
                    # Root password
                    if 'rootPassword' in manager:
                        credentials.append({
                            'hostname': hostname,
                            'username': 'root',
                            'password': manager['rootPassword'],
                            'credentialType': 'SSH',
                            'accountType': 'USER',
                            'resourceType': 'SDDC_MANAGER',
                            'source': 'VCF_INSTALLER'
                        })
                    
                    # Admin@local user (UI/API access)
                    if 'localUserPassword' in manager:
                        credentials.append({
                            'hostname': hostname,
                            'username': 'admin@local',
                            'password': manager['localUserPassword'],
                            'credentialType': 'API',
                            'accountType': 'SERVICE',
                            'resourceType': 'SDDC_MANAGER',
                            'source': 'VCF_INSTALLER'
                        })
                    
                    # VCF user (SSH access)
                    if 'localUserPassword' in manager:
                        credentials.append({
                            'hostname': hostname,
                            'username': 'vcf',
                            'password': manager['localUserPassword'],
                            'credentialType': 'SSH',
                            'accountType': 'SERVICE',
                            'resourceType': 'SDDC_MANAGER',
                            'source': 'VCF_INSTALLER'
                        })
                    
                    # SSH password (if different from localUserPassword)
                    if 'sshPassword' in manager and manager.get('sshPassword') != manager.get('localUserPassword'):
                        credentials.append({
                            'hostname': hostname,
                            'username': 'vcf',
                            'password': manager['sshPassword'],
                            'credentialType': 'SSH',
                            'accountType': 'SERVICE',
                            'resourceType': 'SDDC_MANAGER',
                            'source': 'VCF_INSTALLER'
                        })
                except Exception as e:
                    logger.error(f"Error parsing SDDC Manager credentials: {e}", exc_info=True)
            
            # Parse VCF Operations (Aria Operations) credentials
            if 'vcfOperationsSpec' in spec_data:
                try:
                    ops_spec = spec_data['vcfOperationsSpec']
                    load_balancer_fqdn = ops_spec.get('loadBalancerFqdn', '')
                    
                    # Admin user password (for UI/API access)
                    if 'adminUserPassword' in ops_spec and load_balancer_fqdn:
                        credentials.append({
                            'hostname': load_balancer_fqdn,
                            'username': 'admin',
                            'password': ops_spec['adminUserPassword'],
                            'credentialType': 'API',
                            'accountType': 'SERVICE',
                            'resourceType': 'ARIA_OPERATIONS',
                            'source': 'VCF_INSTALLER'
                        })
                    
                    # Node-specific root passwords
                    if 'nodes' in ops_spec:
                        for node in ops_spec['nodes']:
                            try:
                                node_hostname = node.get('hostname', '')
                                node_type = node.get('type', 'unknown')
                                
                                if 'rootUserPassword' in node:
                                    credentials.append({
                                        'hostname': node_hostname,
                                        'username': 'root',
                                        'password': node['rootUserPassword'],
                                        'credentialType': 'SSH',
                                        'accountType': 'USER',
                                        'resourceType': f'ARIA_OPERATIONS_{node_type.upper()}',
                                        'source': 'VCF_INSTALLER'
                                    })
                            except Exception as e:
                                logger.error(f"Error parsing Aria Operations node credentials for {node_hostname}: {e}", exc_info=True)
                                continue
                except Exception as e:
                    logger.error(f"Error parsing VCF Operations credentials: {e}", exc_info=True)
            
            # Parse VCF Operations Fleet Management (Aria Operations for Networks) credentials
            if 'vcfOperationsFleetManagementSpec' in spec_data:
                try:
                    fleet_spec = spec_data['vcfOperationsFleetManagementSpec']
                    hostname = fleet_spec.get('hostname', '')
                    
                    # Root password
                    if 'rootUserPassword' in fleet_spec:
                        credentials.append({
                            'hostname': hostname,
                            'username': 'root',
                            'password': fleet_spec['rootUserPassword'],
                            'credentialType': 'SSH',
                            'accountType': 'USER',
                            'resourceType': 'ARIA_OPERATIONS_NETWORKS',
                            'source': 'VCF_INSTALLER'
                        })
                    
                    # Admin password
                    if 'adminUserPassword' in fleet_spec:
                        credentials.append({
                            'hostname': hostname,
                            'username': 'admin',
                            'password': fleet_spec['adminUserPassword'],
                            'credentialType': 'API',
                            'accountType': 'SERVICE',
                            'resourceType': 'ARIA_OPERATIONS_NETWORKS',
                            'source': 'VCF_INSTALLER'
                        })
                except Exception as e:
                    logger.error(f"Error parsing Fleet Management credentials: {e}", exc_info=True)
            
            # Parse VCF Operations Collector (Aria Operations for Logs) credentials
            if 'vcfOperationsCollectorSpec' in spec_data:
                try:
                    collector_spec = spec_data['vcfOperationsCollectorSpec']
                    hostname = collector_spec.get('hostname', '')
                    
                    # Root password
                    if 'rootUserPassword' in collector_spec:
                        credentials.append({
                            'hostname': hostname,
                            'username': 'root',
                            'password': collector_spec['rootUserPassword'],
                            'credentialType': 'SSH',
                            'accountType': 'USER',
                            'resourceType': 'ARIA_OPERATIONS_LOGS',
                            'source': 'VCF_INSTALLER'
                        })
                except Exception as e:
                    logger.error(f"Error parsing Operations Collector credentials: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error in _parse_installer_spec: {e}", exc_info=True)
        
        return credentials
    
    def fetch_from_manager(self, host: str, username: str, password: str, ssl_verify: bool = False) -> List[Dict]:
        """Fetch credentials from SDDC Manager"""
        # Get token
        token = self._get_token(host, username, password, ssl_verify)
        
        # Get credentials
        url = f"https://{host}/v1/credentials"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        response = self.session.get(url, headers=headers, verify=ssl_verify, timeout=self.timeout)
        response.raise_for_status()
        credentials = response.json().get("elements", [])
        
        logger.debug(f"Found {len(credentials)} credentials from SDDC Manager {host}")
        
        # Format credentials
        formatted_creds = []
        for cred in credentials:
            formatted_creds.append({
                'hostname': cred.get('resource', {}).get('resourceName', ''),
                'username': cred.get('username', ''),
                'password': cred.get('password', ''),
                'credentialType': cred.get('credentialType', 'USER'),
                'accountType': cred.get('accountType', 'USER'),
                'resourceType': cred.get('resource', {}).get('resourceType', ''),
                'domainName': cred.get('resource', {}).get('domainName', ''),
                'source': 'SDDC_MANAGER'
            })
        
        return formatted_creds

