import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from database import db_manager

logger = logging.getLogger(__name__)

class RewardsSystem:
    def __init__(self, bot):
        self.bot = bot
        self.positive_keywords = [
               
            'mulțumesc', 'thanks', 'mulțumiri', 'apreciez', 'felicitări', 'bravo', 
            'excelent', 'minunat', 'frumos', 'bună idee', 'ajutor', 'respect',
            'îmi pare rău', 'scuze', 'îmi cer scuze', 'congratulări', 'felicit',
            'susțin', 'sunt de acord', 'înțeleg', 'ai dreptate', 'bun punct',
            'interesant', 'util', 'instructiv', 'educativ', 'inspiring',
               
            'thank you', 'thanks', 'appreciate', 'congratulations', 'awesome',
            'excellent', 'wonderful', 'great idea', 'helpful', 'respect',
            'sorry', 'apologize', 'my apologies', 'well done', 'good point',
            'interesting', 'useful', 'educational', 'inspiring', 'support'
        ]
        
        self.positive_patterns = [
            'cum pot să ajut', 'pot să te ajut', 'să colaborăm', 'să lucrăm împreună',
            'să discutăm', 'să ne înțelegem', 'să găsim o soluție', 'să rezolvăm',
            'how can I help', 'can I help', 'let\'s collaborate', 'work together',
            'let\'s discuss', 'let\'s understand', 'find a solution', 'let\'s solve'
        ]

    async def analyze_positive_behavior(self, message_content: str, user_history: List = None) -> Dict:
        """Analizează comportamentul pozitiv în mesaj"""
        content_lower = message_content.lower()
        
        analysis = {
            'is_positive': False,
            'score': 0.0,
            'categories': [],
            'points_earned': 0,
            'feedback_type': 'none'
        }
        
           
        positive_words_found = []
        for keyword in self.positive_keywords:
            if keyword in content_lower:
                positive_words_found.append(keyword)
                analysis['score'] += 0.1
        
           
        positive_patterns_found = []
        for pattern in self.positive_patterns:
            if pattern in content_lower:
                positive_patterns_found.append(pattern)
                analysis['score'] += 0.2
        
           
        if len(message_content) > 50 and '?' in message_content:
            analysis['score'] += 0.1
            analysis['categories'].append('constructive_question')
        
        if len(message_content) > 100 and any(word in content_lower for word in ['pentru că', 'deoarece', 'because', 'since']):
            analysis['score'] += 0.15
            analysis['categories'].append('detailed_explanation')
        
           
        if analysis['score'] >= 0.3:
            analysis['is_positive'] = True
            
               
            if analysis['score'] >= 0.7:
                analysis['points_earned'] = 10
                analysis['feedback_type'] = 'exceptional'
                analysis['categories'].append('exceptional_behavior')
            elif analysis['score'] >= 0.5:
                analysis['points_earned'] = 5
                analysis['feedback_type'] = 'helpful'
                analysis['categories'].append('helpful_behavior')
            else:
                analysis['points_earned'] = 2
                analysis['feedback_type'] = 'positive'
                analysis['categories'].append('positive_behavior')
        
        return analysis

    async def award_points(self, user_id: str, username: str, guild_id: str, points: int, reason: str):
        """Acordă puncte utilizatorului"""
        async with await db_manager.get_connection() as db:
               
            cursor = await db.execute("""
                SELECT total_points, positive_messages, last_reward 
                FROM user_rewards 
                WHERE user_id = ? AND guild_id = ?
            """, (user_id, guild_id))
            
            result = await cursor.fetchone()
            
            if result:
                total_points, positive_messages, last_reward = result
                new_total = total_points + points
                new_messages = positive_messages + 1
                
                await db.execute("""
                    UPDATE user_rewards 
                    SET total_points = ?, positive_messages = ?, last_reward = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ?
                """, (new_total, new_messages, datetime.utcnow().isoformat(), user_id, guild_id))
            else:
                   
                await db.execute("""
                    INSERT INTO user_rewards 
                    (user_id, username, guild_id, total_points, positive_messages, 
                     last_reward, created_at)
                    VALUES (?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                """, (user_id, username, guild_id, points, datetime.utcnow().isoformat()))
            
               
            await db.execute("""
                INSERT INTO reward_transactions 
                (user_id, guild_id, points, reason, timestamp)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, guild_id, points, reason))
            
            await db.commit()
            
               
            await self.check_milestones(user_id, guild_id, new_total if result else points)

    async def check_milestones(self, user_id: str, guild_id: str, total_points: int):
        """Verifică și acordă recompense milestone"""
        milestones = {
            50: {'role': 'Helpful Member', 'badge': '🌟'},
            100: {'role': 'Community Helper', 'badge': '⭐'},
            250: {'role': 'Super Helper', 'badge': '💫'},
            500: {'role': 'Community Champion', 'badge': '🏆'},
            1000: {'role': 'Elite Member', 'badge': '👑'}
        }
        
           
        for milestone, reward in milestones.items():
            if total_points >= milestone:
                   
                async with await db_manager.get_connection() as db:
                    cursor = await db.execute("""
                        SELECT id FROM milestone_rewards 
                        WHERE user_id = ? AND guild_id = ? AND milestone = ?
                    """, (user_id, guild_id, milestone))
                    
                    if not await cursor.fetchone():
                           
                        await db.execute("""
                            INSERT INTO milestone_rewards 
                            (user_id, guild_id, milestone, role_name, badge, achieved_at)
                            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (user_id, guild_id, milestone, reward['role'], reward['badge']))
                        await db.commit()
                        
                           
                        await self.notify_milestone_achieved(user_id, guild_id, milestone, reward)

    async def notify_milestone_achieved(self, user_id: str, guild_id: str, milestone: int, reward: Dict):
        """Trimite notificare pentru milestone atins"""
        try:
            guild = self.bot.get_guild(int(guild_id))
            user = guild.get_member(int(user_id))
            
            if user and guild:
                embed = discord.Embed(
                    title=f"🎉 Milestone Atins!",
                    description=f"{user.mention} a atins {milestone} puncte de reputație!",
                    color=discord.Color.gold()
                )
                
                embed.add_field(name="Recompensă", value=f"{reward['badge']} **{reward['role']}**", inline=True)
                embed.add_field(name="Puncte totale", value=str(milestone), inline=True)
                embed.set_footer(text="Continuă să fii un membru exemplar!")
                
                   
                channel = discord.utils.get(guild.channels, name='general') or guild.system_channel
                if channel:
                    await channel.send(embed=embed)
                
                   
                await self.assign_role(user, reward['role'])
                
        except Exception as e:
            logger.error(f"Eroare la notificarea milestone: {e}")

    async def assign_role(self, user: discord.Member, role_name: str):
        """Acordă rol utilizatorului"""
        try:
            guild = user.guild
            role = discord.utils.get(guild.roles, name=role_name)
            
            if not role:
                   
                role = await guild.create_role(
                    name=role_name,
                    color=discord.Color.green(),
                    mentionable=True,
                    reason="Recompensă automată pentru comportament pozitiv"
                )
            
            await user.add_roles(role, reason="Milestone de reputație atins")
            logger.info(f"Rol {role_name} acordat utilizatorului {user.display_name}")
            
        except discord.Forbidden:
            logger.warning(f"Nu am permisiunea să acord rolul {role_name}")
        except Exception as e:
            logger.error(f"Eroare la acordarea rolului: {e}")

    async def send_positive_feedback(self, message: discord.Message, analysis: Dict):
        """Trimite feedback pozitiv utilizatorului"""
        feedback_messages = {
            'positive': [
                "🌟 Mesaj pozitiv detectat! +{points} puncte de reputație!",
                "✨ Apreciez atitudinea ta constructivă! +{points} puncte!",
                "🙂 Mulțumim pentru contribuția pozitivă! +{points} puncte!"
            ],
            'helpful': [
                "🌟 Mesaj foarte util pentru comunitate! +{points} puncte!",
                "💡 Excelentă contribuție! Continua așa! +{points} puncte!",
                "🤝 Spiritul tău de ajutor este apreciat! +{points} puncte!"
            ],
            'exceptional': [
                "🏆 Comportament exemplar! Ești un model pentru comunitate! +{points} puncte!",
                "👑 Contribuție excepțională! Mulțumim pentru dedicare! +{points} puncte!",
                "🌟 Acest tip de mesaj face comunitatea mai bună! +{points} puncte!"
            ]
        }
        
        feedback_type = analysis['feedback_type']
        points = analysis['points_earned']
        
        if feedback_type in feedback_messages:
            message_template = feedback_messages[feedback_type][
                hash(message.author.id) % len(feedback_messages[feedback_type])
            ]
            feedback_text = message_template.format(points=points)
            
               
            await message.add_reaction('⭐')
            
               
            feedback_msg = await message.channel.send(
                f"{message.author.mention} {feedback_text}",
                delete_after=10
            )

    async def get_leaderboard(self, guild_id: str, limit: int = 10) -> List[Dict]:
        """Obține clasamentul utilizatorilor pozitivi"""
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT user_id, username, total_points, positive_messages,
                       (SELECT COUNT(*) FROM milestone_rewards mr 
                        WHERE mr.user_id = ur.user_id AND mr.guild_id = ur.guild_id) as milestones
                FROM user_rewards ur 
                WHERE guild_id = ? 
                ORDER BY total_points DESC 
                LIMIT ?
            """, (guild_id, limit))
            
            results = await cursor.fetchall()
            
            leaderboard = []
            for i, result in enumerate(results):
                leaderboard.append({
                    'position': i + 1,
                    'user_id': result[0],
                    'username': result[1],
                    'total_points': result[2],
                    'positive_messages': result[3],
                    'milestones': result[4]
                })
            
            return leaderboard

    async def get_user_profile(self, user_id: str, guild_id: str) -> Dict:
        """Obține profilul complet al utilizatorului"""
        async with await db_manager.get_connection() as db:
               
            cursor = await db.execute("""
                SELECT total_points, positive_messages, created_at 
                FROM user_rewards 
                WHERE user_id = ? AND guild_id = ?
            """, (user_id, guild_id))
            
            user_data = await cursor.fetchone()
            
            if not user_data:
                return None
            
               
            cursor = await db.execute("""
                SELECT milestone, role_name, badge, achieved_at 
                FROM milestone_rewards 
                WHERE user_id = ? AND guild_id = ? 
                ORDER BY milestone ASC
            """, (user_id, guild_id))
            
            milestones = await cursor.fetchall()
            
               
            cursor = await db.execute("""
                SELECT points, reason, timestamp 
                FROM reward_transactions 
                WHERE user_id = ? AND guild_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            """, (user_id, guild_id))
            
            transactions = await cursor.fetchall()
            
            return {
                'total_points': user_data[0],
                'positive_messages': user_data[1],
                'member_since': user_data[2],
                'milestones': [
                    {
                        'milestone': m[0],
                        'role': m[1],
                        'badge': m[2],
                        'achieved_at': m[3]
                    } for m in milestones
                ],
                'recent_transactions': [
                    {
                        'points': t[0],
                        'reason': t[1],
                        'timestamp': t[2]
                    } for t in transactions
                ]
            }

   
rewards_system = None

def init_rewards_system(bot):
    """Inițializează sistemul de recompense"""
    global rewards_system
    rewards_system = RewardsSystem(bot)
    return rewards_system