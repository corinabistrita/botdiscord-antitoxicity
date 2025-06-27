import discord
import logging
from datetime import datetime, timedelta
import json
import re

logger = logging.getLogger(__name__)

class EscalationSystem:
    """Sistem de escaladare pentru moderare - DOAR LOGICA DE DECIZIE"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.whitelist = {}     
        
           
        self.escalation_levels = {
            1: {
                'action': 'warning',
                'duration': 0,
                'emoji': '📚',     
                'color': discord.Color.blue(),     
                'description': 'Prima abatere - îndrumăre educațională blândă'
            },
            2: {
                'action': 'final_warning',
                'duration': 0,
                'emoji': '⚠️',
                'color': discord.Color.orange(),
                'description': 'A doua abatere - avertisment mai serios'
            },
            3: {
                'action': 'timeout',
                'duration': 300,     
                'emoji': '🔇',
                'color': discord.Color.red(),
                'description': 'A treia abatere - timeout scurt pentru reflecție'
            },
            4: {
                'action': 'timeout',
                'duration': 1800,     
                'emoji': '🔇',
                'color': discord.Color.red(),
                'description': 'A patra abatere - timeout mediu'
            },
            5: {
                'action': 'timeout',
                'duration': 3600,     
                'emoji': '🔇',
                'color': discord.Color.dark_red(),
                'description': 'A cincea abatere - timeout lung'
            },
            6: {
                'action': 'temp_ban',
                'duration': 86400,     
                'emoji': '🔨',
                'color': discord.Color.from_rgb(139, 0, 0),
                'description': 'A șasea abatere - ban temporar pentru comportament persistent'
            }
        }
        
        self.educational_templates = {
            'toxicity': {
                'title': 'Limbaj Care Poate Răni',
                'main_message': 'Mesajul tău conținea cuvinte care pot răni sau deranja alte persoane.',
                'explanation': 'Știm că probabil nu ai avut intenții rele, dar cuvintele pot afecta starea emoțională a celorlalți membri din comunitate.',
                'suggestions': [
                    'Încearcă să îți exprimi opinia fără cuvinte negative',
                    'Folosește fraze de tipul "Nu sunt de acord cu..." în loc de atacuri',
                    'Ia o pauză scurtă înainte de a răspunde când ești supărat',
                    'Gândește-te cum te-ai simți tu în locul celuilalt'
                ]
            },
            'harassment': {
                'title': 'Comunicare Neprieteoasă',
                'main_message': 'Mesajul tău a fost perceput ca fiind neprieteinos către alt membru.',
                'explanation': 'O comunicare respectuoasă face comunitatea mai plăcută pentru toți. Credem că ai intenții bune!',
                'suggestions': [
                    'Concentrează-te pe idei, nu pe persoane',
                    'Folosește formulări de tipul "Eu cred că..." în loc de "Tu ești..."',
                    'Respectă diversitatea de opinii - toți avem perspective diferite',
                    'Încearcă să găsești ceva pozitiv în ceea ce spune cealaltă persoană'
                ]
            },
            'spam': {
                'title': 'Mesaje Repetitive',
                'main_message': 'Am observat mesaje repetitive care pot deranja conversația.',
                'explanation': 'Mesajele repetitive fac dificilă urmărirea discuțiilor importante pentru ceilalți membri.',
                'suggestions': [
                    'Trimite un singur mesaj clar în loc de mai multe',
                    'Editează mesajul anterior dacă vrei să adaugi ceva',
                    'Respectă ritmul conversației și lasă și alții să răspundă',
                    'Dacă nu primești răspuns imediat, încearcă să fii răbdător'
                ]
            },
            'hate_speech': {
                'title': 'Limbaj de Excludere',
                'main_message': 'Mesajul tău conținea limbaj care poate exclude sau jigni anumite grupuri.',
                'explanation': 'Comunitatea noastră valorează diversitatea și respectul mutual. Astfel de mesaje pot face pe cineva să se simtă neprimit.',
                'suggestions': [
                    'Respectă toate persoanele indiferent de diferențele lor',
                    'Exprimă-ți dezacordul în mod civilizat și constructiv',
                    'Consideră că diversitatea de opinii ne face mai puternici ca comunitate',
                    'Încearcă să înțelegi perspectivele diferite de a ta'
                ]
            },
            'threat': {
                'title': 'Limbaj Amenințător',
                'main_message': 'Mesajul tău a fost perceput ca având un ton amenințător.',
                'explanation': 'Amenințările, chiar și în glumă, pot face pe alții să se simtă neconfortabil sau în nesiguranță.',
                'suggestions': [
                    'Exprimă-ți frustrarea în mod constructiv',
                    'Folosește canalele oficiale pentru a raporta probleme serioase',
                    'Ia o pauză dacă ești foarte supărat - e normal să ai emoții intense',
                    'Încearcă să găsești soluții în loc să exprimi amenințări'
                ]
            },
            'general': {
                'title': 'Comunicare de Îmbunătățit',
                'main_message': 'Mesajul tău poate fi îmbunătățit pentru o comunicare mai pozitivă.',
                'explanation': 'O comunicare respectuoasă și pozitivă face comunitatea mai plăcută pentru toți membrii.',
                'suggestions': [
                    'Citește din nou regulile comunității când ai timp',
                    'Gândește-te cum te-ai simți tu în locul celuilalt',
                    'Contribuie pozitiv la discuții cu idei constructive',
                    'Încearcă să găsești ceva pozitiv în fiecare interacțiune'
                ]
            }
        }
        
           
        self.extreme_categories = [
            'threat_serious',         
            'doxxing',               
            'hate_speech_severe',    
            'harassment_severe',     
            'illegal_content',       
            'nsfw_explicit'          
        ]
        
           
        self.extreme_keywords = [
            'să te omor', 'să te ucid', 'să te găsesc acasă', 'să te violez',
            'adresa ta este', 'știu unde stai', 'să te rănesc grav', 'să-ți fac rău',
            'să-ți arăt eu', 'să te distrug', 'să te termin', 'vin după tine'
        ]

    async def load_whitelist(self, guild_id: str):
        """Încarcă whitelist-ul pentru un server"""
        try:
            async with await self.db_manager.get_connection() as db:
                cursor = await db.execute("""
                    SELECT user_id FROM whitelist 
                    WHERE guild_id = ? AND is_active = 1
                """, (guild_id,))
                
                whitelist_users = await cursor.fetchall()
                self.whitelist[guild_id] = [row[0] for row in whitelist_users]
                
                logger.info(f"📋 Încărcat {len(self.whitelist[guild_id])} utilizatori în whitelist pentru guild {guild_id}")
                
        except Exception as e:
            logger.error(f"💥 Eroare la încărcarea whitelist-ului pentru {guild_id}: {e}")
            self.whitelist[guild_id] = []

    def is_user_whitelisted(self, user_id: str, guild_id: str) -> bool:
        """Verifică dacă un utilizator este în whitelist"""
        return user_id in self.whitelist.get(guild_id, [])

    async def get_recent_violations(self, user_id: str, guild_id: str, hours: int = 24) -> int:
        """LOGICA: Obține numărul de abateri recente pentru calculul nivelului"""
        try:
            async with await self.db_manager.get_connection() as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM moderated_messages 
                    WHERE user_id = ? AND guild_id = ? 
                    AND is_toxic = 1 
                    AND timestamp >= datetime('now', '-{} hours')
                """.format(hours), (user_id, guild_id))
                
                result = await cursor.fetchone()
                violations = result[0] if result else 0
                
                logger.info(f"📊 Utilizator {user_id}: {violations} abateri în ultimele {hours}h")
                return violations
                
        except Exception as e:
            logger.error(f"💥 Eroare la obținerea abaterilor pentru {user_id}: {e}")
            return 0

    def is_extreme_violation(self, analysis: dict) -> bool:
        """LOGICA: Verifică dacă este o abatere extremă care merită ban imediat - VERSIUNEA CORECTATĂ"""
        
           
        if analysis.get('category') in self.extreme_categories:
            logger.info(f"🚨 Categorie extremă CONFIRMATĂ: {analysis.get('category')}")
            return True
        
           
        if analysis['confidence'] > 0.98 and analysis.get('severity') == 'extreme':
            logger.info(f"🚨 Toxicitate extremă CONFIRMATĂ: confidence {analysis['confidence']:.2%}")
            return True
        
           
        original_text = analysis.get('original_text', '').lower()
        for keyword in self.extreme_keywords:
            if keyword in original_text:
                logger.info(f"🚨 Cuvânt cheie EXTREM detectat: {keyword}")
                return True
        
           
        logger.info(f"ℹ️ Nu este abatere extremă - va fi procesată normal")
        return False

    async def determine_action(self, message, analysis: dict) -> dict:
        """LOGICA PRINCIPALĂ: Determină acțiunea bazată pe istoricul și severitatea mesajului - VERSIUNEA CORECTATĂ"""
        
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        
        logger.info(f"🤔 DETERMINARE ACȚIUNE pentru {message.author.display_name}")
        logger.info(f"   Categorie: {analysis['category']}")
        logger.info(f"   Încredere: {analysis['confidence']:.2%}")
        
           
        if self.is_user_whitelisted(user_id, guild_id):
            logger.info(f"✅ Utilizator în whitelist - scăpat de moderare")
            return {
                'level': 0,
                'action': 'whitelist_skip',
                'duration': 0,
                'violations': 0,
                'emoji': '✅',
                'message': 'Utilizator în whitelist'
            }
        
           
        if self.is_extreme_violation(analysis):
            logger.info(f"🚨 CAZ EXTREM DETECTAT - Ban permanent imediat")
            return {
                'level': 7,     
                'action': 'ban',
                'duration': 0,     
                'violations': 999,     
                'emoji': '🔨',
                'message': 'Abatere extremă - ban permanent',
                'educational_message': 'Comportament extrem de toxic care pune în pericol siguranța comunității.'
            }
        
           
        violations_24h = await self.get_recent_violations(user_id, guild_id, hours=24)
        
           
        escalation_level = violations_24h + 1     
        
           
        escalation_level = min(escalation_level, 6)
        
        logger.info(f"📈 ESCALADARE CALCULATĂ CORECT:")
        logger.info(f"   Abateri anterioare 24h: {violations_24h}")
        logger.info(f"   Nivel pentru această abatere: {escalation_level}")
        logger.info(f"   Prima abatere: {'DA' if violations_24h == 0 else 'NU'}")
        
           
        level_config = self.escalation_levels[escalation_level].copy()
        
           
        if escalation_level <= 3:
            logger.info(f"📚 Nivel educațional ({escalation_level}) - fără ajustări pentru severitate")
        elif escalation_level >= 4 and analysis.get('severity') == 'high':
               
            escalation_level = min(escalation_level + 1, 6)
            level_config = self.escalation_levels[escalation_level].copy()
            logger.info(f"⬆️ Escaladare mărită pentru severitate mare: nivel {escalation_level}")
        
           
        educational_message = await self.create_educational_message(
            analysis['category'], 
            escalation_level
        )
        
        result = {
            'level': escalation_level,
            'action': level_config['action'],
            'duration': level_config['duration'],
            'violations': violations_24h,     
            'emoji': level_config['emoji'],
            'message': level_config['description'],
            'educational_message': educational_message.get('main_message', ''),
            'color': level_config['color']
        }
        
        logger.info(f"✅ DECIZIE FINALĂ CORECTATĂ: {result}")
        
        return result

    async def determine_action_preview(self, user_id: str, guild_id: str, analysis: dict) -> dict:
        """LOGICA: Preview pentru comenzi - nu afectează istoricul real"""
        
           
        if self.is_user_whitelisted(user_id, guild_id):
            return {
                'level': 0,
                'action': 'whitelist_skip',
                'violations': 0
            }
        
           
        if self.is_extreme_violation(analysis):
            return {
                'level': 7,
                'action': 'ban',
                'violations': 999
            }
        
           
        violations_24h = await self.get_recent_violations(user_id, guild_id, hours=24)
        escalation_level = min(violations_24h + 1, 6)
        level_config = self.escalation_levels[escalation_level]
        
        return {
            'level': escalation_level,
            'action': level_config['action'],
            'violations': violations_24h
        }

    async def create_educational_message(self, category: str, level: int) -> dict:
        """LOGICA: Creează mesajul educațional bazat pe categorie și nivel - VERSIUNEA BLÂNDĂ"""
        
           
        template = self.educational_templates.get(category, self.educational_templates['general'])
        
           
        if level == 1:
            intensity = "Am observat că mesajul tău poate fi îmbunătățit."
            tone = "Aceasta este doar o îndrumăre prietenoasă pentru a ne ajuta să păstrăm o atmosferă plăcută."
        elif level == 2:
            intensity = "Este a doua oară când observăm o problemă similară."
            tone = "Te rugăm să fii mai atent la modul în care comunici - mulțumim pentru înțelegere!"
        elif level == 3:
            intensity = f"Este a {level}-a abatere și trebuie să fim mai fermi."
            tone = "Vei primi o pauză scurtă pentru a reflecta asupra comunicării."
        elif level >= 4:
            intensity = f"Este a {level}-a abatere și comportamentul trebuie schimbat urgent."
            tone = "Măsurile devin mai stricte pentru a proteja comunitatea."
        else:
            intensity = "Comportament neadecvat detectat."
            tone = "Te rugăm să îmbunătățești modul de comunicare."
        
        return {
            'title': template['title'],
            'main_message': f"{intensity} {template['main_message']}",
            'explanation': template['explanation'],
            'suggestions': template['suggestions'],
            'tone': tone,
            'level': level,
            'category': category
        }

    async def get_color_for_level(self, level: int) -> discord.Color:
        """LOGICA: Returnează culoarea pentru nivel de escaladare"""
        level_config = self.escalation_levels.get(level, self.escalation_levels[1])
        return level_config['color']

    async def get_action_for_level(self, level: int) -> dict:
        """LOGICA: Returnează acțiunea pentru un nivel dat"""
        return self.escalation_levels.get(level, self.escalation_levels[1])

    async def get_user_stats(self, user_id: str, guild_id: str) -> dict:
        """LOGICA: Obține statistici complete pentru un utilizator"""
        try:
            violations_24h = await self.get_recent_violations(user_id, guild_id, 24)
            violations_7d = await self.get_recent_violations(user_id, guild_id, 168)     
            
               
            async with await self.db_manager.get_connection() as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM moderated_messages 
                    WHERE user_id = ? AND guild_id = ? AND is_toxic = 1
                """, (user_id, guild_id))
                
                result = await cursor.fetchone()
                total_violations = result[0] if result else 0
            
               
            current_level = min(violations_24h + 1, 6) if violations_24h > 0 else 0
            
            return {
                'violations_24h': violations_24h,
                'violations_7d': violations_7d,
                'total_violations': total_violations,
                'current_level': current_level,
                'is_whitelisted': self.is_user_whitelisted(user_id, guild_id),
                'risk_level': self._calculate_risk_level(violations_24h, violations_7d)
            }
            
        except Exception as e:
            logger.error(f"💥 Eroare la obținerea statisticilor pentru {user_id}: {e}")
            return {
                'violations_24h': 0,
                'violations_7d': 0,
                'total_violations': 0,
                'current_level': 0,
                'is_whitelisted': False,
                'risk_level': 'low'
            }

    def _calculate_risk_level(self, violations_24h: int, violations_7d: int) -> str:
        """LOGICA: Calculează nivelul de risc al utilizatorului"""
        if violations_24h >= 4:
            return 'critical'     
        elif violations_24h >= 2:
            return 'high'         
        elif violations_7d >= 3:
            return 'medium'       
        elif violations_7d >= 1:
            return 'low'          
        else:
            return 'none'         

    async def add_to_whitelist(self, user_id: str, guild_id: str, added_by: str, reason: str = None):
        """LOGICA: Adaugă un utilizator în whitelist"""
        try:
            async with await self.db_manager.get_connection() as db:
                await db.execute("""
                    INSERT OR REPLACE INTO whitelist 
                    (user_id, guild_id, added_by, reason, added_at, is_active)
                    VALUES (?, ?, ?, ?, datetime('now'), 1)
                """, (user_id, guild_id, added_by, reason or 'Adăugat manual'))
                
                await db.commit()
            
               
            if guild_id not in self.whitelist:
                self.whitelist[guild_id] = []
            
            if user_id not in self.whitelist[guild_id]:
                self.whitelist[guild_id].append(user_id)
            
            logger.info(f"✅ Utilizator {user_id} adăugat în whitelist pentru guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"💥 Eroare la adăugarea în whitelist: {e}")
            return False

    async def remove_from_whitelist(self, user_id: str, guild_id: str, removed_by: str):
        """LOGICA: Elimină un utilizator din whitelist"""
        try:
            async with await self.db_manager.get_connection() as db:
                await db.execute("""
                    UPDATE whitelist 
                    SET is_active = 0, removed_by = ?, removed_at = datetime('now')
                    WHERE user_id = ? AND guild_id = ?
                """, (removed_by, user_id, guild_id))
                
                await db.commit()
            
               
            if guild_id in self.whitelist and user_id in self.whitelist[guild_id]:
                self.whitelist[guild_id].remove(user_id)
            
            logger.info(f"❌ Utilizator {user_id} eliminat din whitelist pentru guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"💥 Eroare la eliminarea din whitelist: {e}")
            return False

    async def reset_user_violations(self, user_id: str, guild_id: str, reset_by: str):
        """LOGICA: Resetează abaterile unui utilizator (grațiere)"""
        try:
            async with await self.db_manager.get_connection() as db:
                   
                await db.execute("""
                    UPDATE moderated_messages 
                    SET is_reset = 1, reset_by = ?, reset_at = datetime('now')
                    WHERE user_id = ? AND guild_id = ? AND is_toxic = 1
                """, (reset_by, user_id, guild_id))
                
                await db.commit()
            
            logger.info(f"🔄 Abateri resetate pentru utilizator {user_id} în guild {guild_id} de către {reset_by}")
            return True
            
        except Exception as e:
            logger.error(f"💥 Eroare la resetarea abaterilor: {e}")
            return False

    async def get_escalation_stats(self, guild_id: str, days: int = 30) -> dict:
        """LOGICA: Obține statistici despre escaladare pentru un server"""
        try:
            async with await self.db_manager.get_connection() as db:
                   
                cursor = await db.execute("""
                    SELECT 
                        CASE 
                            WHEN is_toxic = 0 THEN 0
                            ELSE (
                                SELECT COUNT(*) FROM moderated_messages m2 
                                WHERE m2.user_id = m1.user_id 
                                AND m2.guild_id = m1.guild_id 
                                AND m2.is_toxic = 1 
                                AND m2.timestamp <= m1.timestamp
                                AND m2.timestamp >= datetime('now', '-1 day')
                            )
                        END as level,
                        COUNT(*) as count
                    FROM moderated_messages m1
                    WHERE guild_id = ? 
                    AND timestamp >= datetime('now', '-{} days')
                    AND is_toxic = 1
                    GROUP BY level
                    ORDER BY level
                """.format(days), (guild_id,))
                
                level_stats = {}
                total_violations = 0
                
                async for row in cursor:
                    level = min(row[0] + 1, 6)     
                    count = row[1]
                    level_stats[level] = count
                    total_violations += count
                
                return {
                    'total_violations': total_violations,
                    'level_distribution': level_stats,
                    'most_common_level': max(level_stats.items(), key=lambda x: x[1])[0] if level_stats else 1,
                    'escalation_rate': len([l for l in level_stats.keys() if l >= 4]) / max(len(level_stats), 1),
                    'whitelist_count': len(self.whitelist.get(guild_id, []))
                }
                
        except Exception as e:
            logger.error(f"💥 Eroare la obținerea statisticilor de escaladare: {e}")
            return {
                'total_violations': 0,
                'level_distribution': {},
                'most_common_level': 1,
                'escalation_rate': 0.0,
                'whitelist_count': 0
            }

    def get_level_description(self, level: int) -> str:
        """LOGICA: Returnează descrierea pentru un nivel de escaladare"""
        level_config = self.escalation_levels.get(level, self.escalation_levels[1])
        return level_config['description']

    def format_duration(self, seconds: int) -> str:
        """UTILITAR: Formatează durata în text citibil"""
        if seconds == 0:
            return "N/A"
        elif seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds//60}m"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h" if hours > 0 else f"{days}d"