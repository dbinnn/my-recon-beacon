import platform
import os
import socket
import json
import subprocess
import datetime
import psutil
import getpass
import re

class SystemRecon:
    def __init__(self):
        self.data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "os": self._get_os_info(),
            "network": self._get_network_info(),
            "hardware": self._get_hardware_info(),
            "processes": self._get_process_summary(),
            "security": self._get_security_context(),
            "environment": self._get_environment_info(),
            "disk_usage": self._get_disk_usage()
        }
        self._add_raw_output()

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
                "bytes_recv": io_counters.bytes_recv,
                "packets_sent": io_counters.packets_sent,
                "packets_recv": io_counters.packets_recv
            }
        }

        for iface, addrs in interfaces.items():
            net_info["interfaces"][iface] = [
                {
                    "family": "IPv4" if addr.family == 2 else "IPv6" if addr.family == 10 else "Other",
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                }
            ]
            
        for iface, stats in stats.items():
            net_info["stats"][iface] = {
                "isup": stats.isup,
                "speed": stats.speed,
                "duplex": stats.duplex
            }
            
        return net_info

    def _get_hardware_info(self):
        cpu_freq = psutil.cpu_freq()
        cpu_times = psutil.cpu_times()
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        
        return {
            "cpu": {
                "count": psutil.cpu_count(logical=True),
                "count_physical": psutil.cpu_count(logical=False),
                "percent": psutil.cpu_percent(interval=1),
                "freq": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None
                },
                "times": {
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "idle": cpu_times.idle
                }
            },
            "memory": {
                "total_bytes": virtual_mem.total,
                "available_bytes": virtual_mem.available,
                "percent_used": virtual_mem.percent,
                "swap_total": swap_mem.total,
                "swap_used": swap_mem.used
            },
            "boot_time": psutil.boot_time()
        }

    def _get_process_summary(self):
        # Limit to top 20 processes by memory to keep payload size manageable
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent', 'username', 'cmdline']):
            try:
                procs.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "memory_percent": p.info['memory_percent'],
                    "cpu_percent": p.info['cpu_percent'],
                    "username": p.info['username'],
                    "cmdline": p.info['cmdline']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        procs.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        return procs[:20]

    def _get_security_context(self):
        return {
            "current_user": getpass.getuser(),
            "uid": os.getuid() if hasattr(os, 'getuid') else None,
            "euid": os.geteuid() if hasattr(os, 'geteuid') else None,
            "groups": os.getgroups() if hasattr(os, 'getgroups') else None,
            "is_root": os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        }

    def _get_environment_info(self):
        # Filter sensitive env vars but keep relevant ones
        env_keys = ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'PWD', 'EDITOR', 'PYTHONPATH']
        return {k: os.environ.get(k) for k in env_keys if os.environ.get(k)}

    def _get_disk_usage(self):
        partitions = []
        for part in psutil.disk_partitions(all=True):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": usage.total / (1024**3),
                    "used_gb": usage.used / (1024**3),
                    "free_gb": usage.free / (1024**3),
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue
        return partitions

    def _add_raw_output(self):
        # Execute system-specific commands for detailed raw info
        commands = {
            "uname": "uname -a",
            "whoami": "whoami",
            "ifconfig": "ifconfig" if os.name == 'posix' else "ipconfig /all",
            "ps": "ps aux | head -n 20" if os.name == 'posix' else "tasklist"
        }
        
        raw = {}
        for key, cmd in commands.items():
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                raw[key] = result.stdout.strip()[:2000] # Limit output size
            except Exception as e:
                raw[key] = f"Error executing {cmd}: {str(e)}"
        
        self.data["raw_system_output"] = raw

    def export(self, filename="recon_report.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, default=str)
        print(f"[+] Recon complete. Report saved to {filename}")
        print(json.dumps(self.data, indent=4, default=str))

if __name__ == "__main__":
    recon = SystemRecon()
    recon.export()