import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import aiosqlite

class DatabaseManager:
    def __init__(self, db_path: str = "moderation_bot.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    async def init_database(self):
        """Inițializează baza de date cu toate tabelele necesare și migration"""
        async with aiosqlite.connect(self.db_path) as db:
               
            await self._migrate_schema(db)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS moderated_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    toxicity_scores TEXT NOT NULL,
                    is_toxic BOOLEAN NOT NULL,
                    category TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    warning_count INTEGER DEFAULT 0,
                    mute_count INTEGER DEFAULT 0,
                    ban_count INTEGER DEFAULT 0,
                    last_violation DATETIME,
                    risk_level TEXT DEFAULT 'low',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS server_config (
                    guild_id TEXT PRIMARY KEY,
                    toxicity_threshold REAL DEFAULT 0.7,
                    auto_moderation BOOLEAN DEFAULT TRUE,
                    log_channel_id TEXT,
                    admin_role_id TEXT,
                    language TEXT DEFAULT 'ro',
                    strict_mode BOOLEAN DEFAULT FALSE,
                    educational_feedback BOOLEAN DEFAULT TRUE,
                    rewards_enabled BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    total_messages INTEGER DEFAULT 0,
                    toxic_messages INTEGER DEFAULT 0,
                    positive_messages INTEGER DEFAULT 0,
                    warnings_issued INTEGER DEFAULT 0,
                    mutes_issued INTEGER DEFAULT 0,
                    bans_issued INTEGER DEFAULT 0,
                    points_awarded INTEGER DEFAULT 0,
                    UNIQUE(guild_id, date)
                )
            """)
            
               
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    total_points INTEGER DEFAULT 0,
                    positive_messages INTEGER DEFAULT 0,
                    last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id)
                )
            """)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    total_points INTEGER DEFAULT 0,
                    positive_messages INTEGER DEFAULT 0,
                    last_reward DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id)
                )
            """)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reward_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS milestone_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    milestone INTEGER NOT NULL,
                    role_name TEXT NOT NULL,
                    badge TEXT NOT NULL,
                    achieved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id, milestone)
                )
            """)
            
               
            await db.execute("""
                CREATE TABLE IF NOT EXISTS positive_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    points_earned INTEGER NOT NULL,
                    categories TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
            self.logger.info("Baza de date inițializată cu succes!")
    
    async def _migrate_schema(self, db):
        """Migrează schema bazei de date pentru a adăuga coloane lipsă"""
        try:
               
            cursor = await db.execute("PRAGMA table_info(server_config)")
            columns = await cursor.fetchall()
            existing_columns = [col[1] for col in columns]
            
               
            if 'educational_feedback' not in existing_columns:
                await db.execute("ALTER TABLE server_config ADD COLUMN educational_feedback BOOLEAN DEFAULT TRUE")
                self.logger.info("Adăugată coloana 'educational_feedback' în server_config")
            
            if 'rewards_enabled' not in existing_columns:
                await db.execute("ALTER TABLE server_config ADD COLUMN rewards_enabled BOOLEAN DEFAULT TRUE")
                self.logger.info("Adăugată coloana 'rewards_enabled' în server_config")
            
            await db.commit()
            
        except Exception as e:
            self.logger.warning(f"Migration schema: {e}")
    
       
       
       
    
    async def add_user(self, user_id: str, username: str, guild_id: str = None):
        """Adaugă un utilizator nou în sistem"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT OR IGNORE INTO users (user_id, username, guild_id)
                    VALUES (?, ?, ?)
                """, (user_id, username, guild_id or 'default'))
                await db.commit()
                self.logger.info(f"Utilizator {username} ({user_id}) adăugat")
            except Exception as e:
                self.logger.error(f"Eroare la adăugarea utilizatorului {user_id}: {e}")
    
    async def get_user(self, user_id: str, guild_id: str = None):
        """Obține informații despre un utilizator"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id, username, guild_id, total_points, positive_messages, 
                       last_active, created_at
                FROM users 
                WHERE user_id = ? AND guild_id = ?
            """, (user_id, guild_id or 'default'))
            
            result = await cursor.fetchone()
            
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'guild_id': result[2],
                    'total_points': result[3],
                    'positive_messages': result[4],
                    'last_active': result[5],
                    'created_at': result[6]
                }
            return None
    
    async def update_user_points(self, user_id: str, points: int, guild_id: str = None):
        """Actualizează punctele unui utilizator"""
        async with aiosqlite.connect(self.db_path) as db:
               
            user = await self.get_user(user_id, guild_id)
            if not user:
                   
                await db.execute("""
                    INSERT INTO users (user_id, username, guild_id, total_points)
                    VALUES (?, ?, ?, ?)
                """, (user_id, f"User_{user_id[:8]}", guild_id or 'default', points))
            else:
                   
                await db.execute("""
                    UPDATE users 
                    SET total_points = total_points + ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ?
                """, (points, user_id, guild_id or 'default'))
            
            await db.commit()
    
    async def get_user_list(self, guild_id: str = None, limit: int = 50):
        """Obține lista utilizatorilor"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id, username, total_points, positive_messages, created_at
                FROM users 
                WHERE guild_id = ?
                ORDER BY total_points DESC
                LIMIT ?
            """, (guild_id or 'default', limit))
            
            results = await cursor.fetchall()
            
            return [
                {
                    'user_id': row[0],
                    'username': row[1],
                    'total_points': row[2],
                    'positive_messages': row[3],
                    'created_at': row[4]
                }
                for row in results
            ]
    
       
       
       
    
    async def log_positive_message(self, message_data: Dict):
        """Înregistrează un mesaj pozitiv"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO positive_messages 
                (user_id, username, guild_id, channel_id, message_content, 
                 points_earned, categories)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message_data['user_id'],
                message_data['username'],
                message_data['guild_id'],
                message_data.get('channel_id', ''),
                message_data['message_content'],
                message_data['points_earned'],
                json.dumps(message_data['categories'])
            ))
            await db.commit()
    
    async def get_connection(self):
        """Obține conexiune la baza de date pentru utilizare externă"""
        return aiosqlite.connect(self.db_path)
    
       
       
       
    
    async def log_moderated_message(self, message_data: Dict):
        """Înregistrează un mesaj moderat în baza de date"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO moderated_messages 
                (user_id, username, guild_id, channel_id, message_content, 
                 toxicity_scores, is_toxic, category, action_taken, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_data['user_id'],
                message_data['username'],
                message_data['guild_id'],
                message_data['channel_id'],
                message_data['message_content'],
                json.dumps(message_data['toxicity_scores']),
                message_data['is_toxic'],
                message_data['category'],
                message_data['action_taken'],
                message_data['confidence']
            ))
            await db.commit()
    
    async def update_user_warnings(self, user_id: str, username: str, guild_id: str, action: str):
        """Actualizează statisticile de avertismente pentru utilizator"""
        async with aiosqlite.connect(self.db_path) as db:
               
            cursor = await db.execute("""
                SELECT warning_count, mute_count, ban_count FROM user_warnings 
                WHERE user_id = ? AND guild_id = ?
            """, (user_id, guild_id))
            
            result = await cursor.fetchone()
            
            if result:
                   
                warning_count, mute_count, ban_count = result
                
                if action == "warning":
                    warning_count += 1
                elif action == "mute":
                    mute_count += 1
                elif action == "ban":
                    ban_count += 1
                
                   
                total_violations = warning_count + mute_count * 2 + ban_count * 5
                if total_violations >= 10:
                    risk_level = "high"
                elif total_violations >= 5:
                    risk_level = "medium"
                else:
                    risk_level = "low"
                
                await db.execute("""
                    UPDATE user_warnings 
                    SET warning_count = ?, mute_count = ?, ban_count = ?,
                        last_violation = CURRENT_TIMESTAMP, risk_level = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ?
                """, (warning_count, mute_count, ban_count, risk_level, user_id, guild_id))
            else:
                   
                warning_count = 1 if action == "warning" else 0
                mute_count = 1 if action == "mute" else 0
                ban_count = 1 if action == "ban" else 0
                
                await db.execute("""
                    INSERT INTO user_warnings 
                    (user_id, username, guild_id, warning_count, mute_count, ban_count, 
                     last_violation, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'low')
                """, (user_id, username, guild_id, warning_count, mute_count, ban_count))
            
            await db.commit()
    
    async def get_server_config(self, guild_id: str) -> Dict:
        """Obține configurația pentru server"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM server_config WHERE guild_id = ?
            """, (guild_id,))
            
            result = await cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            else:
                   
                default_config = {
                    'guild_id': guild_id,
                    'toxicity_threshold': 0.7,
                    'auto_moderation': True,
                    'log_channel_id': None,
                    'admin_role_id': None,
                    'language': 'ro',
                    'strict_mode': False,
                    'educational_feedback': True,
                    'rewards_enabled': True
                }
                await self.save_server_config(default_config)
                return default_config
    
    async def save_server_config(self, config: Dict):
        """Salvează configurația serverului"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO server_config 
                (guild_id, toxicity_threshold, auto_moderation, log_channel_id, 
                 admin_role_id, language, strict_mode, educational_feedback,
                 rewards_enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                config['guild_id'],
                config['toxicity_threshold'],
                config['auto_moderation'],
                config.get('log_channel_id'),
                config.get('admin_role_id'),
                config['language'],
                config['strict_mode'],
                config.get('educational_feedback', True),
                config.get('rewards_enabled', True)
            ))
            await db.commit()
    
    async def get_dashboard_stats(self, guild_id: str, days: int = 7) -> Dict:
        """Obține statistici pentru dashboard"""
        async with aiosqlite.connect(self.db_path) as db:
               
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN is_toxic = 1 THEN 1 ELSE 0 END) as toxic_messages,
                    SUM(CASE WHEN action_taken = 'warning' THEN 1 ELSE 0 END) as warnings,
                    SUM(CASE WHEN action_taken = 'mute' THEN 1 ELSE 0 END) as mutes,
                    SUM(CASE WHEN action_taken = 'ban' THEN 1 ELSE 0 END) as bans
                FROM moderated_messages 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-{} days')
            """.format(days), (guild_id,))
            
            stats = await cursor.fetchone()
            
               
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as positive_messages,
                    SUM(points_earned) as points_awarded
                FROM positive_messages 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-{} days')
            """.format(days), (guild_id,))
            
            positive_stats = await cursor.fetchone()
            
               
            cursor = await db.execute("""
                SELECT user_id, username, warning_count, mute_count, ban_count, risk_level
                FROM user_warnings 
                WHERE guild_id = ? 
                ORDER BY (warning_count + mute_count * 2 + ban_count * 5) DESC
                LIMIT 10
            """, (guild_id,))
            
            risky_users = await cursor.fetchall()
            
               
            cursor = await db.execute("""
                SELECT user_id, username, total_points
                FROM users 
                WHERE guild_id = ?
                ORDER BY total_points DESC
                LIMIT 10
            """, (guild_id,))
            
            top_positive_users = await cursor.fetchall()
            
               
            cursor = await db.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_toxic = 1 THEN 1 ELSE 0 END) as toxic
                FROM moderated_messages 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-{} days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """.format(days), (guild_id,))
            
            daily_activity = await cursor.fetchall()
            
            return {
                'total_messages': stats[0] or 0,
                'toxic_messages': stats[1] or 0,
                'warnings': stats[2] or 0,
                'mutes': stats[3] or 0,
                'bans': stats[4] or 0,
                'positive_messages': positive_stats[0] or 0,
                'points_awarded': positive_stats[1] or 0,
                'risky_users': [
                    {
                        'user_id': user[0],
                        'username': user[1],
                        'warnings': user[2],
                        'mutes': user[3],
                        'bans': user[4],
                        'risk_level': user[5]
                    } for user in risky_users
                ],
                'top_positive_users': [
                    {
                        'user_id': user[0],
                        'username': user[1],
                        'points': user[2]
                    } for user in top_positive_users
                ],
                'daily_activity': [
                    {
                        'date': day[0],
                        'total': day[1],
                        'toxic': day[2]
                    } for day in daily_activity
                ]
            }

   
db_manager = DatabaseManager()
