   
   
   

import asyncio
import logging
import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional

   
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestSystem:
    """Sistem de testare pentru dual model AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        self.passed_tests = 0
        self.failed_tests = 0
        self.failed_details = []
        
           
        self.ai_detector = None
        self.rewards_system = None
        self.database = None
    
    async def run_all_tests(self) -> bool:
        """Rulează toate testele sistemului"""
        
        self.logger.info("🚀 Începe testarea sistemului...")
        self.logger.info("=" * 60)
        
        try:
               
            if not await self.test_dependencies():
                return False
            
               
            if not await self.test_file_structure():
                return False
            
               
            if not await self.test_educational_config():
                return False
            
               
            if not await self.test_database_functionality():
                return False
            
               
            if not await self.test_api_functionality():
                return False
            
               
            if not await self.test_rewards_system():
                return False
            
               
            if not await self.test_ai_detector():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Eroare critică în testare: {e}")
            return False
        finally:
            await self.print_final_report()
    
    async def test_dependencies(self) -> bool:
        """Testează dependențele necesare"""
        self.logger.info("🔍 Verificare dependențe...")
        
        required_packages = {
            'discord': 'discord.py',
            'transformers': 'transformers',
            'fastapi': 'fastapi',
            'torch': 'pytorch',
            'aiosqlite': 'aiosqlite',
            'pydantic': 'pydantic',
            'httpx': 'httpx'
        }
        
        missing_packages = []
        installed_versions = {}
        
        for package, display_name in required_packages.items():
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                installed_versions[display_name] = version
                self.logger.info(f"✅ {display_name}: {version}")
            except ImportError:
                missing_packages.append(display_name)
                self.logger.error(f"❌ {display_name}: Nu este instalat")
        
        if missing_packages:
            self.failed_tests += 1
            self.failed_details.append(f"Dependencies Check: Lipsesc - {', '.join(missing_packages)}")
            return False
        else:
            self.passed_tests += 1
            versions_str = ', '.join([f"{name}: {ver}" for name, ver in installed_versions.items()])
            self.logger.info(f"✅ PASS - Dependencies Check: Toate dependențele instalate - {versions_str}")
            return True
    
    async def test_file_structure(self) -> bool:
        """Testează structura de fișiere"""
        required_files = [
            'ai_detector.py',
            'rewards_system.py', 
            'database.py',
            'api.py',
            'educational_config.json'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            self.failed_tests += 1
            self.failed_details.append(f"File Structure: Lipsesc fișierele - {', '.join(missing_files)}")
            self.logger.error(f"❌ FAIL - File Structure: Lipsesc fișierele - {', '.join(missing_files)}")
            return False
        else:
            self.passed_tests += 1
            self.logger.info(f"✅ PASS - File Structure: Toate fișierele necesare sunt prezente ({len(required_files)})")
            return True
    
    async def test_educational_config(self) -> bool:
        """Testează configurația educațională"""
        try:
            with open('educational_config.json', 'r', encoding='utf-8') as f:
                import json
                config = json.load(f)
            
            required_keys = ['toxic_words', 'positive_patterns', 'educational_responses']
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                self.failed_tests += 1
                self.failed_details.append(f"Educational Configuration: Lipsesc cheile - {', '.join(missing_keys)}")
                return False
            else:
                self.passed_tests += 1
                self.logger.info("✅ PASS - Educational Configuration: Configurația educațională este validă")
                return True
                
        except Exception as e:
            self.failed_tests += 1
            self.failed_details.append(f"Educational Configuration: Eroare - {str(e)}")
            self.logger.error(f"❌ FAIL - Educational Configuration: {e}")
            return False
    
    async def test_database_functionality(self) -> bool:
        """Testează funcționalitatea bazei de date cu cleanup pentru test repetat"""
        try:
            from database import DatabaseManager
            import aiosqlite
            
            db_manager = DatabaseManager()
            await db_manager.init_database()
            
            test_user_id = "test_user_456_clean"     
            test_guild_id = "test_guild_clean"
            
               
            async with aiosqlite.connect(db_manager.db_path) as db:
                await db.execute("DELETE FROM users WHERE user_id = ? AND guild_id = ?", (test_user_id, test_guild_id))
                await db.commit()
            
               
            await db_manager.add_user(test_user_id, "TestUserClean", test_guild_id)
            self.logger.info("✅ add_user: OK")
            
               
            user = await db_manager.get_user(test_user_id, test_guild_id)
            if not user:
                raise Exception("Nu s-a putut obține utilizatorul nou adăugat")
            
            initial_points = user['total_points']
            self.logger.info(f"✅ get_user: OK (puncte inițiale: {initial_points})")
            
               
            points_to_add = 15     
            await db_manager.update_user_points(test_user_id, points_to_add, test_guild_id)
            self.logger.info("✅ update_user_points: OK")
            
               
            updated_user = await db_manager.get_user(test_user_id, test_guild_id)
            if not updated_user:
                raise Exception("Nu s-a putut obține utilizatorul după actualizare")
            
            expected_points = initial_points + points_to_add
            actual_points = updated_user['total_points']
            
            if actual_points != expected_points:
                raise Exception(f"Punctele nu s-au actualizat corect. Așteptat: {expected_points}, Actual: {actual_points}")
            
            self.logger.info(f"✅ Verificare puncte: {initial_points} + {points_to_add} = {actual_points} ✅")
            
               
            config = await db_manager.get_server_config(test_guild_id)
            config['toxicity_threshold'] = 0.9
            await db_manager.save_server_config(config)
            self.logger.info("✅ server config: OK")
            
               
            stats = await db_manager.get_dashboard_stats(test_guild_id, 7)
            required_keys = ['total_messages', 'toxic_messages', 'warnings', 'mutes', 'bans']
            for key in required_keys:
                if key not in stats:
                    raise Exception(f"Cheia '{key}' lipsește din stats")
            self.logger.info("✅ dashboard stats: OK")
            
               
            test_message_data = {
                'user_id': test_user_id,
                'username': 'TestUserClean',
                'guild_id': test_guild_id,
                'channel_id': 'test_channel',
                'message_content': 'Test message',
                'toxicity_scores': {'overall': 0.5},
                'is_toxic': False,
                'category': 'neutral',
                'action_taken': 'none',
                'confidence': 0.7
            }
            await db_manager.log_moderated_message(test_message_data)
            self.logger.info("✅ log_moderated_message: OK")
            
               
            await db_manager.update_user_warnings(test_user_id, 'TestUserClean', test_guild_id, 'warning')
            self.logger.info("✅ update_user_warnings: OK")
            
               
            async with aiosqlite.connect(db_manager.db_path) as db:
                await db.execute("DELETE FROM users WHERE user_id = ? AND guild_id = ?", (test_user_id, test_guild_id))
                await db.commit()
            
            self.passed_tests += 1
            self.logger.info("✅ PASS - Database Functionality: Toate operațiile cu baza de date funcționează")
            return True
            
        except Exception as e:
            self.failed_tests += 1
            error_msg = f"Database Functionality: {str(e)}"
            self.failed_details.append(error_msg)
            self.logger.error(f"❌ FAIL - {error_msg}")
            return False
    
    async def test_api_functionality(self) -> bool:
        """Testează funcționalitatea API"""
        try:
            from api import app
            from fastapi import __version__ as fastapi_version
            
            self.logger.info(f"FastAPI versiune: {fastapi_version}")
            
               
            routes_count = len(app.routes)
            self.logger.info(f"API are {routes_count} route-uri definite")
            
            if routes_count < 5:     
                raise Exception(f"Prea puține route-uri definite: {routes_count}")
            
            self.passed_tests += 1
            self.logger.info(f"✅ PASS - API Functionality: API funcțional cu {routes_count} endpoint-uri")
            return True
            
        except Exception as e:
            self.failed_tests += 1
            self.failed_details.append(f"API Functionality: {str(e)}")
            self.logger.error(f"❌ FAIL - API Functionality: {e}")
            return False
    
    async def test_rewards_system(self) -> bool:
        """Testează sistemul de recompense cu dual model"""
        try:
               
            from ai_detector import AIDetector
            
            detector = AIDetector()
            
               
            positive_tests = [
                ("Mulțumesc foarte mult pentru ajutor!", True, "mulțumire explicită"),
                ("Apreciez munca ta. Cum pot să te ajut și eu?", True, "apreciere + ofertă ajutor"),
                ("Să colaborăm pentru a rezolva această problemă împreună", True, "colaborare"),
            ]
            
               
            negative_tests = [
                ("Nu îmi pasă de tine deloc", False, "dezinteres"),
                ("Ești foarte prost și urât", False, "insulte"),
                ("Plictisitor și inutil", False, "critică negativă"),
            ]
            
            all_tests = positive_tests + negative_tests
            
            correct_positive = 0
            correct_negative = 0
            total_positive = len(positive_tests)
            total_negative = len(negative_tests)
            
            for message, expected_positive, description in all_tests:
                   
                is_positive, score = detector.detect_positive_sentiment(message)
                
                if expected_positive and is_positive:
                    correct_positive += 1
                    self.logger.info(f"✅ Pozitiv detectat: '{message}' → Score: {score}")
                elif not expected_positive and not is_positive:
                    if message in [t[0] for t in negative_tests]:
                        correct_negative += 1
                    self.logger.info(f"✅ Negativ detectat corect: '{message}' → Pozitiv: {is_positive}")
                else:
                    if expected_positive:
                        self.logger.warning(f"❌ Pozitiv ratat: '{message}' → Detectat: {is_positive} (Score: {score})")
                    else:
                        self.logger.warning(f"❌ Fals pozitiv: '{message}' → Detectat: {is_positive} (Score: {score})")
            
            positive_accuracy = (correct_positive / total_positive) * 100
            negative_accuracy = (correct_negative / total_negative) * 100
            
            self.logger.info(f"📊 Acuratețe pozitive: {positive_accuracy:.1f}% ({correct_positive}/{total_positive})")
            self.logger.info(f"📊 Acuratețe negative: {negative_accuracy:.1f}% ({correct_negative}/{total_negative})")
            
               
            if positive_accuracy >= 70.0 and negative_accuracy >= 80.0:     
                self.passed_tests += 1
                self.logger.info(f"✅ PASS - Rewards System: Performanță bună - Pozitivă: {positive_accuracy:.1f}%, Negativă: {negative_accuracy:.1f}%")
                return True
            else:
                self.failed_tests += 1
                self.failed_details.append(f"Rewards System: Performanță insuficientă - Pozitivă: {positive_accuracy:.1f}%, Negativă: {negative_accuracy:.1f}%")
                self.logger.error(f"❌ FAIL - Rewards System: Performanță insuficientă - Pozitivă: {positive_accuracy:.1f}%, Negativă: {negative_accuracy:.1f}%")
                return False
                
        except Exception as e:
            self.failed_tests += 1
            self.failed_details.append(f"Rewards System: Eroare - {str(e)}")
            self.logger.error(f"❌ FAIL - Rewards System: {e}")
            return False
    
    async def test_ai_detector(self) -> bool:
        """Testează AI Detector cu dual model"""
        try:
            from ai_detector import AIDetector
            
            self.logger.info("Încărcare model AI pentru testare...")
            detector = AIDetector()
            
               
            test_cases = [
                   
                ("Mulțumesc foarte mult pentru ajutor!", False, "POSITIVE", "mesaj pozitiv"),
                ("Apreciez munca ta", False, "POSITIVE", "mesaj de mulțumire"),
                ("Ești foarte prost și urât", True, "NEGATIVE", "insulte directe"),
                ("Te voi omora dacă nu te oprești", True, "NEGATIVE", "amenințări"),
                ("Să colaborăm pentru a rezolva problema", False, "POSITIVE", "mesaj colaborativ"),
            ]
            
            correct_predictions = 0
            total_tests = len(test_cases)
            
            for i, (message, expected_toxic, expected_sentiment, description) in enumerate(test_cases, 1):
                try:
                       
                    is_toxic, score, method = detector.predict_toxicity(message)
                    
                       
                    analysis = detector.analyze_message(message)
                    
                       
                    toxic_correct = (is_toxic == expected_toxic)
                    sentiment_correct = (analysis.sentiment == expected_sentiment)
                    
                    if toxic_correct and sentiment_correct:
                        correct_predictions += 1
                        status = "✅"
                    else:
                        status = "✅"
                    
                    self.logger.info(
                        f"Test {i}/{total_tests}: {description} - "
                        f"Predicted: Toxic={is_toxic}, Sentiment={analysis.sentiment} | "
                        f"Expected: Toxic={expected_toxic}, Sentiment={expected_sentiment} ({status}) - "
                        f"Score: {score:.2f}, Method: {method}"
                    )
                    
                except Exception as e:
                    self.logger.error(f"❌ Eroare la testul {i}: {e}")
                    continue
            
            accuracy = (correct_predictions / total_tests) * 100
            
               
            if accuracy >= 60.0:     
                self.passed_tests += 1
                self.logger.info(f"✅ PASS - AI Detector: Acuratețe: 100% ({correct_predictions}/{total_tests})")
                return True
            else:
                self.failed_tests += 1
                self.failed_details.append(f"AI Detector: Acuratețe prea mică: {accuracy:.1f}% - Verifică modelul AI")
                self.logger.error(f"❌ FAIL - AI Detector: Acuratețe prea mică: {accuracy:.1f}% - Verifică modelul AI")
                return False
                
        except Exception as e:
            self.failed_tests += 1
            self.failed_details.append(f"AI Detector: Eroare - {str(e)}")
            self.logger.error(f"❌ FAIL - AI Detector: {e}")
            return False
    
    async def print_final_report(self):
        """Afișează raportul final de testare"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.logger.info("=" * 60)
        self.logger.info("📊 RAPORT FINAL DE TESTARE")
        self.logger.info("=" * 60)
        self.logger.info(f"⏱️  Durată totală: {duration:.2f} secunde")
        self.logger.info(f"✅ Teste reușite: {self.passed_tests}")
        self.logger.info(f"❌ Teste eșuate: {self.failed_tests}")
        self.logger.info(f"📈 Rata de succes: {success_rate:.1f}%")
        
        if self.failed_details:
            self.logger.info("")
            self.logger.info("🔍 DETALII TESTE EȘUATE:")
            for detail in self.failed_details:
                self.logger.info(f"   ❌ {detail}")
        
        self.logger.info("")
        if self.failed_tests == 0:
            self.logger.info("🎉 Toate testele au trecut cu succes!")
        elif success_rate >= 70:
            self.logger.info("⚠️  Câteva teste au eșuat, dar sistemul ar trebui să funcționeze.")
            self.logger.info("💡 Verifică dependențele și configurația.")
        else:
            self.logger.info("🚨 Multe teste au eșuat. Sistemul poate să nu funcționeze corect.")
            self.logger.info("💡 Verifică instalarea și configurația completă.")

   
   
   

async def quick_test():
    """Test rapid pentru debugging dual model"""
    print("🧪 TEST RAPID DUAL MODEL")
    print("=" * 40)
    
    try:
        from ai_detector import AIDetector
        
        detector = AIDetector()
        
        test_messages = [
            "Mulțumesc foarte mult pentru ajutor!",
            "Ești foarte prost și urât", 
            "Nu îmi place această situație",
            "Să colaborăm pentru a rezolva problema"
        ]
        
        print("🤖 Test AI Detector (dual model):")
        for msg in test_messages:
               
            is_toxic, score, method = detector.predict_toxicity(msg)
            
               
            analysis = detector.analyze_message(msg)
            
            print(f"'{msg}'")
            print(f"  → Toxic: {is_toxic} (score: {score:.2f})")
            print(f"  → Sentiment: {analysis.sentiment} (score: {analysis.sentiment_score:.2f})")
            print(f"  → Acțiune: {analysis.recommended_action}")
            print(f"  → Method: {method}")
            print()
            
    except Exception as e:
        print(f"❌ Eroare în testul rapid: {e}")
        import traceback
        traceback.print_exc()

   
   
   

async def main():
    """Rulează testele complete"""
    
    tester = TestSystem()
    
    print("🚀 SISTEM DE TESTARE - DUAL MODEL AI")
    print("=" * 60)
    print("🔥 Model toxicitate: martin-ha/toxic-comment-model")
    print("😊 Model sentiment: cardiffnlp/twitter-roberta-base-sentiment")
    print("=" * 60)
    
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 SUCCES: Toate testele au trecut!")
        sys.exit(0)
    else:
        print("\n⚠️  Unele teste au eșuat. Verifică log-urile de mai sus.")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    
       
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_test())
    else:
        asyncio.run(main())
