   
"""
🤖 Discord AI Moderation Bot - Script principal de pornire FIXED
"""

import asyncio
import logging
import os
import sys
import threading
import time
import json
import signal
from pathlib import Path
from datetime import datetime

   
def setup_logging():
    """Configurează logging-ul pentru întregul sistem"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
       
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
       
    file_handler = logging.FileHandler(
        f'logs/moderation_bot_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
       
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    
       
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=[file_handler, console_handler]
    )

       
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiosqlite').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

class SystemManager:
    """Manager pentru întregul sistem de moderare"""
    
    def __init__(self):
        self.api_process = None
        self.bot_task = None
        self.is_running = False
        self.config = self.load_config()
        
    def load_config(self):
        """Încarcă configurația sistemului"""
        try:
            with open('educational_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("Configurația educațională încărcată cu succes!")
            return config
        except FileNotFoundError:
            logger.warning("Fișierul educational_config.json nu a fost găsit!")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Eroare la parsarea configurației: {e}")
            return {}

    def load_env(self):
        """Încarcă variabilele de mediu din .env"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("Fișier .env încărcat")
        except ImportError:
            logger.warning("python-dotenv nu este instalat. Folosește variabile de mediu sistem.")

    def check_environment(self):
        """Verifică dacă environment-ul este configurat corect"""
        logger.info("Verificare environment...")
        
           
        self.load_env()
        
           
        if sys.version_info < (3, 8):
            logger.error("Python 3.8+ este necesar!")
            return False
        
        logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        
           
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if not discord_token:
            logger.error("DISCORD_BOT_TOKEN nu este setat!")
            logger.info("\nPASUL 1: Creează un fișier .env în directorul principal")
            logger.info("PASUL 2: Adaugă în .env linia:")
            logger.info("DISCORD_BOT_TOKEN=token_aici")
            logger.info("\nSau setează variabila de mediu:")
            logger.info("Windows: set DISCORD_BOT_TOKEN=token_aici")
            logger.info("Linux/Mac: export DISCORD_BOT_TOKEN=token_aici")
            return False
        
        logger.info("Token Discord găsit")
        
           
        try:
            import discord
            import transformers
            import fastapi
            import aiosqlite
            import torch
            logger.info("Toate dependențele critice sunt instalate!")
        except ImportError as e:
            logger.error(f"Dependență lipsă: {e}")
            logger.info("Rulează: pip install -r requirements.txt")
            return False
        
           
        try:
            if torch.cuda.is_available():
                logger.info(f"GPU detectat: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Rulare pe CPU (recomandat GPU pentru performanță)")
        except Exception as e:
            logger.warning(f"Nu s-a putut verifica GPU: {e}")
        
        return True

    def create_dashboard_files(self):
        """Creează fișierele pentru dashboard dacă nu există"""
        dashboard_dir = Path("dashboard")
        dashboard_dir.mkdir(exist_ok=True)
        
           
        required_files = ['index.html', 'style.css', 'script.js']
        missing_files = []
        
        for file_name in required_files:
            file_path = dashboard_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            logger.warning(f"Fișiere dashboard lipsă: {missing_files}")
               
            self.create_placeholder_dashboard()
        else:
            logger.info("Toate fișierele dashboard sunt prezente")

    def create_placeholder_dashboard(self):
        """Creează un dashboard placeholder minimal"""
        dashboard_dir = Path("dashboard")
        
           
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Discord Bot Dashboard</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>Discord Moderation Bot Dashboard</h1>
    <p>Dashboard în dezvoltare...</p>
</body>
</html>"""
        
        with open(dashboard_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
           
        with open(dashboard_dir / "style.css", "w", encoding="utf-8") as f:
            f.write("body { font-family: Arial, sans-serif; }")
        
           
        with open(dashboard_dir / "script.js", "w", encoding="utf-8") as f:
            f.write("console.log('Dashboard loaded');")

    async def check_system_health(self):
        """Verifică sănătatea componentelor sistemului"""
        logger.info("Verificare sănătate sistem...")
        
        health_status = {
            'database': False,
            'ai_model': False,
            'rewards_system': False,
            'educational_config': False
        }
        
        try:
               
            from database import db_manager
            await db_manager.init_database()
            health_status['database'] = True
            logger.info("Baza de date: OK")
            
               
            from ai_detector import AIDetector
            detector = AIDetector()
            health_status['ai_model'] = True
            logger.info("Model AI: OK")
            
               
            from rewards_system import RewardsSystem
            rewards = RewardsSystem(None)
            health_status['rewards_system'] = True
            logger.info("Sistem recompense: OK")
            
               
            if self.config and 'educational_strategies' in self.config:
                health_status['educational_config'] = True
                logger.info("Configurație educațională: OK")
            
        except Exception as e:
            logger.error(f"Eroare la verificarea sănătății: {e}")
            return False
        
           
        healthy_components = sum(health_status.values())
        total_components = len(health_status)
        
        if healthy_components == total_components:
            logger.info(f"Toate componentele sunt sănătoase ({healthy_components}/{total_components})")
            return True
        else:
            logger.warning(f"Componente funcționale: {healthy_components}/{total_components}")
            for component, status in health_status.items():
                if not status:
                    logger.error(f"{component}: NEFUNCȚIONAL")
            return healthy_components >= 3     

    def run_fastapi_server(self):
        """Pornește serverul FastAPI în thread separat"""
        try:
            import uvicorn
            from api import app
            
            logger.info("Pornire server FastAPI pe http://localhost:8000")
            logger.info("Dashboard disponibil la: http://localhost:8000")
            
            uvicorn.run(
                app, 
                host="0.0.0.0", 
                port=8000, 
                log_level="warning",
                access_log=False
            )
        
        except Exception as e:
            logger.error(f"Eroare la pornirea serverului FastAPI: {e}")
            self.is_running = False

    async def run_discord_bot(self):
        """Pornește botul Discord"""
        try:
            from discord_bot import run_bot
            logger.info("Pornire bot Discord...")
            
            await run_bot()
        
        except Exception as e:
            logger.error(f"Eroare la pornirea botului Discord: {e}")
            self.is_running = False

    def handle_shutdown(self, signum, frame):
        """Gestionează închiderea elegantă a sistemului"""
        logger.info(f"Semnal de închidere primit: {signum}")
        self.is_running = False
        
           
        if self.api_process and self.api_process.is_alive():
            logger.info("Oprire server FastAPI...")
            self.api_process.terminate()
            self.api_process.join(timeout=5)
        
           
        if self.bot_task and not self.bot_task.done():
            logger.info("Oprire bot Discord...")
            self.bot_task.cancel()
        
        logger.info("Sistem oprit cu succes!")
        sys.exit(0)

    async def start_system(self):
        """Pornește întregul sistem"""
        logger.info("Inițializare sistem de moderare AI...")
        
           
        if not self.check_environment():
            logger.error("Environment-ul nu este configurat corect!")
            return False
        
        self.create_dashboard_files()
        
           
        if not await self.check_system_health():
            logger.error("Sistemul nu este complet funcțional!")
            response = input("Continui oricum? (y/N): ")
            if response.lower() != 'y':
                return False
        
           
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        self.is_running = True
        
           
        api_thread = threading.Thread(
            target=self.run_fastapi_server,
            daemon=True,
            name="FastAPI-Server"
        )
        api_thread.start()
        self.api_process = api_thread
        
           
        await asyncio.sleep(3)
        
           
        logger.info("Sistem complet inițializat!")
        logger.info("Funcționalități disponibile:")
        logger.info("   • Detectare toxicitate contextuală cu AI")
        logger.info("   • Feedback educațional automatizat")
        logger.info("   • Sistem de recompense pentru comportament pozitiv")
        logger.info("   • Dashboard web modern și interactiv")
        logger.info("   • Anti-bypass pentru încercări de evitare")
        logger.info("   • Progres educațional tracked per utilizator")
        
           
        try:
            await self.run_discord_bot()
        except Exception as e:
            logger.error(f"Eroare critică: {e}")
            self.is_running = False
        
        return True

def show_banner():
    """Afișează banner-ul de pornire"""
       
    banner = """
    ===================================================
              DISCORD AI MODERATION BOT              
                                                     
      Sistem inteligent de moderare cu:             
      - Feedback educational                         
      - Recompense pentru comportament pozitiv      
      - Detectare contextuala cu AI                 
      - Dashboard modern si interactiv               
                                                     
              Versiunea 2.0.0 - 2024                
    ===================================================
    """
    print(banner)

async def main():
    """Funcția principală"""
    show_banner()
    
       
    if len(sys.argv) > 1:
        if sys.argv[1] == '--create-env':
            logger.info("Creare fișier .env...")
            with open('.env', 'w') as f:
                f.write("DISCORD_BOT_TOKEN=.\n\n")
                f.write("LOG_LEVEL=INFO\n")
            logger.info("Fișier .env creat! Editează-l și adaugă token-ul Discord.")
            sys.exit(0)
        
        elif sys.argv[1] == '--health-check':
            logger.info("Rulare verificare sănătate...")
            manager = SystemManager()
            success = await manager.check_system_health()
            sys.exit(0 if success else 1)
        
        elif sys.argv[1] == '--version':
            print("Discord AI Moderation Bot v2.0.0")
            print("Funcționalități: AI Detection, Educational Feedback, Rewards System, Modern Dashboard")
            sys.exit(0)
        
        elif sys.argv[1] == '--help':
            print("Utilizare: python run.py [opțiuni]")
            print("")
            print("Opțiuni:")
            print("  --create-env      Creează fișier .env template")
            print("  --health-check    Verifică sănătatea sistemului")
            print("  --version         Afișează versiunea")
            print("  --help            Afișează acest mesaj")
            print("")
            print("Environment variables necesare:")
            print("  DISCORD_BOT_TOKEN    Token-ul botului Discord")
            print("  LOG_LEVEL           Nivelul de logging (DEBUG, INFO, WARNING, ERROR)")
            sys.exit(0)
    
       
    manager = SystemManager()
    
    try:
        success = await manager.start_system()
        if not success:
            logger.error("Sistemul nu a putut fi pornit!")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Întrerupere de la tastatură...")
    except Exception as e:
        logger.error(f"Eroare neașteptată: {e}")
        sys.exit(1)
    finally:
        logger.info("Închidere sistem...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLa revedere!")
    except Exception as e:
        logger.error(f"Eroare fatală: {e}")
        sys.exit(1)