import discord
from discord.ext import commands
import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
import json
from ai_detector import AIDetector, analyze_message_complete
from database import db_manager
from rewards_system import init_rewards_system, rewards_system
from escalation_system import EscalationSystem

   
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!mod ', intents=intents)

class ModerationBot:
    def __init__(self, bot):
        self.bot = bot
        self.ai_detector = AIDetector()
        self.escalation_system = EscalationSystem(db_manager)
        
           
        self.severity_patterns = {
               
            'mild': {
                'patterns': [
                    r'\bstupid\s+ce[- ]ai\s+scris\b',
                    r'\bnu\s+cred\s+că\s+înțelegi\b',
                    r'\bte\s+documentezi\s+puțin\b',
                    r'\bnu\s+prea\s+ai\s+dreptate\b',
                    r'\bcam\s+greșit\b',
                    r'\bnu\s+e\s+chiar\s+așa\b'
                ],
                'severity': 1,
                'action': 'educational_only'
            },
            
               
            'moderate': {
                'patterns': [
                    r'\bești\s+(cam\s+)?prost\b',
                    r'\btaci\s+(dracu|naiba)\b',
                    r'\bcomentariu.*inutil\b',
                    r'\bnu\s+ai\s+nimic\s+inteligent\b',
                    r'\b(prost|stupid|idiot)\s+dacă\b',
                    r'\bstrici\s+conversația\b'
                ],
                'severity': 2,
                'action': 'warning'
            },
            
               
            'severe': {
                'patterns': [
                    r'\b(sunteți|ești)\s+(niște\s+)?idio[țt]i\b',
                    r'\bretardat\b',
                    r'\bjigodie\b',
                    r'\bmeriți\s+blocat\b',
                    r'\b(toți|toate)\s+.*\s+(proști|idioți)\b',
                    r'\bcum\s+(naiba|dracu)\s+poți\s+fi\b'
                ],
                'severity': 3,
                'action': 'mute + feedback'
            },
            
               
            'extreme': {
                'patterns': [
                    r'\bgunoi\s+uman\b',
                    r'\bsper\s+să\s+pățești\b',
                    r'\bdistrug\s+viața\b',
                    r'\bmeriti\s+să\s+mori\b',
                    r'\bte\s+omor\b',
                    r'\bsinucide[- ]te\b'
                ],
                'severity': 4,
                'action': 'ban temporar + feedback'
            }
        }
        
           
        self.educational_messages = {
            1: {
                'title': '💡 Sugestie prietenoasă',
                'message': (
                    'Am observat că tonul mesajului tău poate fi perceput ca fiind mai dur decât ai intenționat. '
                    'În comunitatea noastră încurajăm exprimarea clară, dar respectuoasă. Îți propunem un mod alternativ de a formula o critică: '
                    '🗨️ *„Nu sunt de acord cu această idee, dar cred că putem discuta mai în detaliu”* în loc de *„Ce prostie!”*.'
                ),
                'tips': [
                    '✨ Reformulează criticile într-un mod constructiv și calm',
                    '🧩 Exemple: „Nu sunt de acord cu ideea ta” în loc de „Nu știi ce vorbești”',
                    '🤝 Încearcă să înțelegi perspectiva celuilalt, chiar dacă nu ești de acord',
                    '🧠 Întreabă-te: cum ar suna acest mesaj dacă l-ai primi tu?'
                ],
                'color': discord.Color.blue()
            },  

            2: {
                'title': '⚠️ Avertisment - Limbaj inadecvat',
                'message': 'Mesajul tău conține limbaj care poate răni sau deranja alți membri. Aceasta este prima ta avertizare.',
                'tips': [
                    '🚫 Evită insultele și atacurile personale',
                    '💬 Exprimă-ți dezacordul fără a jigni',
                    '⏸️ Ia o pauză scurtă înainte de a răspunde când ești supărat'
                ],
                'color': discord.Color.orange()
            },
            3: {
                'title': '🔇 Mute aplicat - Comportament toxic',
                'message': 'Ai  mut temporar din cauza limbajului toxic. Folosește acest timp pentru a te calma.',
                'tips': [
                    '🤔 Reflectează asupra impactului cuvintelor tale',
                    '📚 Recitește regulile comunității',
                    '🔄 Când revii, încearcă o abordare mai pozitivă'
                ],
                'color': discord.Color.red()
            },
            4: {
                'title': '🚨 Acțiune severă - Comportament extrem',
                'message': 'Ești în ban. Comportamentul tău este complet inacceptabil și pune în pericol siguranța comunității.',
                'tips': [
                    '⛔ Acest tip de comportament nu este tolerat',
                    '⚖️ Consecințele pot include ban permanent',
                    '🆘 Dacă ai nevoie de ajutor, contactează un administrator'
                ],
                'color': discord.Color.dark_red()
            }
        }

    def analyze_toxicity_level(self, text: str) -> dict:
        """Analizează nivelul de toxicitate bazat pe pattern-uri"""
        text_lower = text.lower()
        
           
        for level_name, level_data in self.severity_patterns.items():
            for pattern in level_data['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return {
                        'is_toxic': level_data['severity'] >= 2,
                        'severity': level_data['severity'],
                        'action': level_data['action'],
                        'level_name': level_name,
                        'pattern_matched': pattern
                    }
        
           
        return {
            'is_toxic': False,
            'severity': 0,
            'action': None,
            'level_name': 'clean'
        }

    async def send_educational_feedback(self, message, severity_level, duration=None):
        """Trimite feedback educațional adaptat nivelului de severitate"""
        edu_data = self.educational_messages.get(severity_level, self.educational_messages[1])
        
        embed = discord.Embed(
            title=edu_data['title'],
            description=edu_data['message'],
            color=edu_data['color'],
            timestamp=discord.utils.utcnow()
        )
        
           
        embed.add_field(
            name="📌 Cum poți îmbunătăți:",
            value="\n".join(edu_data['tips']),
            inline=False
        )
        
           
        if duration:
            embed.add_field(
                name="⏱️ Durată",
                value=f"Mute pentru {duration} minute",
                inline=True
            )
        
           
        if severity_level == 1:
            embed.set_footer(text="Aceasta este doar o sugestie prietenoasă")
        elif severity_level == 2:
            embed.set_footer(text="Prima avertizare - fii atent la comportament")
        elif severity_level == 3:
            embed.set_footer(text="Mute aplicat - comportament inacceptabil")
        else:
            embed.set_footer(text="Acțiune severă - ultimul avertisment")
        
           
        delete_after = 30 if severity_level == 1 else 60
        await message.channel.send(
            f"{message.author.mention}",
            embed=embed,
            delete_after=delete_after
        )

    async def moderate_message(self, message):
        """Funcția principală de moderare - SIMPLIFICATĂ"""
        try:
            if not message.content or len(message.content.strip()) < 2:
                return
            
            guild_id = str(message.guild.id)
            user_id = str(message.author.id)
            
            logger.info(f"🔍 Analizez: '{message.content}' de la {message.author.display_name}")
            
               
            if self.escalation_system.is_user_whitelisted(user_id, guild_id):
                logger.info("🛡️ Utilizator în whitelist - skip")
                return
            
               
            toxicity_result = self.analyze_toxicity_level(message.content)
            
               
            await db_manager.log_moderated_message({
                'user_id': user_id,
                'username': message.author.display_name,
                'guild_id': guild_id,
                'channel_id': str(message.channel.id),
                'message_content': message.content,
                'toxicity_scores': {'severity': toxicity_result['severity']},
                'is_toxic': toxicity_result['is_toxic'],
                'category': toxicity_result['level_name'],
                'action_taken': toxicity_result['action'],
                'confidence': 0.9 if toxicity_result['severity'] > 0 else 0.1
            })
            
               
            severity = toxicity_result['severity']
            
            if severity == 0:
                   
                logger.info("✅ Mesaj curat")
                return
            
            elif severity == 1:
                   
                logger.info("💡 Nivel 1-3: Feedback educațional")
                await self.send_educational_feedback(message, 1)
            
            elif severity == 2:
                   
                logger.info("⚠️ Nivel 4-6: Warning + feedback")
                await self.send_educational_feedback(message, 2)
                
                   
                await asyncio.sleep(10)
                try:
                    await message.delete()
                except:
                    pass
            
            elif severity == 3:
                   
                logger.info("🔇 Nivel 7-9: Mute + feedback")
                await self.send_educational_feedback(message, 3, duration=10)
                
                   
                await asyncio.sleep(2)
                   
                try:
                    timeout_until = discord.utils.utcnow() + timedelta(minutes=180)
                    await message.author.timeout(
                        timeout_until, 
                        reason=f"Comportament toxic - Nivel {severity}"
                    )
                except discord.Forbidden:
                    await message.channel.send(
                        f"❌ Nu am permisiuni de timeout pentru {message.author.mention}",
                        delete_after=10
                    )
                
                   
                try:
                    await message.delete()
                except:
                    pass
            
            elif severity == 4:
                   
                logger.info("🚨 Nivel 10: Acțiune severă")
                
                   
                user_history = await self.get_user_history(user_id, guild_id, 10)
                toxic_count = sum(1 for h in user_history if h['is_toxic'])
                
                   
                if toxic_count >= 3:
                    await self.send_educational_feedback(message, 4)
                else:
                    await self.send_educational_feedback(message, 4, duration=60)
                
                   
                await asyncio.sleep(2)
                
                if toxic_count >= 3:
                       
                    try:
                        await message.author.ban(
                            reason="Comportament extrem de toxic - amenințări grave",
                            delete_message_days=1
                        )
                        
                        embed = discord.Embed(
                            title="🔨 Ban Permanent",
                            description=f"{message.author.display_name} a fost banat pentru comportament extrem de toxic.",
                            color=discord.Color.dark_red()
                        )
                        await message.channel.send(embed=embed)
                    except discord.Forbidden:
                           
                        timeout_until = discord.utils.utcnow() + timedelta(hours=24)
                        await message.author.timeout(timeout_until, reason="Comportament extrem")
                else:
                       
                    timeout_until = discord.utils.utcnow() + timedelta(hours=1)
                    await message.author.timeout(timeout_until, reason="Comportament extrem")
                
                   
                try:
                    await message.delete()
                except:
                    pass
                
                   
                await self.alert_admins(message, toxicity_result)
            
        except Exception as e:
            logger.error(f"💥 Eroare la moderare: {e}")

    async def alert_admins(self, message, toxicity_result):
        """Alertează administratorii pentru cazuri severe"""
           
        log_channel = message.channel
        
        embed = discord.Embed(
            title="🚨 ALERTĂ MODERARE - Comportament Extrem",
            description=f"Utilizator: {message.author.mention}",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="💬 Mesaj detectat",
            value=f"||{message.content[:200]}...||" if len(message.content) > 200 else f"||{message.content}||",
            inline=False
        )
        
        embed.add_field(name="📍 Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="⚡ Acțiune", value="Verificare admin necesară", inline=True)
        
        embed.set_footer(text="Acțiune automată aplicată - verificați situația")
        
        await log_channel.send(embed=embed)

    async def get_user_history(self, user_id: str, guild_id: str, limit: int = 10) -> list:
        """Obține istoricul utilizatorului"""
        try:
            async with await db_manager.get_connection() as db:
                cursor = await db.execute("""
                    SELECT is_toxic, category, confidence, timestamp 
                    FROM moderated_messages 
                    WHERE user_id = ? AND guild_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, guild_id, limit))
                
                history = await cursor.fetchall()
                return [
                    {
                        'is_toxic': bool(h[0]),
                        'category': h[1],
                        'confidence': h[2],
                        'timestamp': h[3]
                    } for h in history
                ]
        except Exception as e:
            logger.error(f"Eroare la obținerea istoricului: {e}")
            return []

   
moderator = None

@bot.event
async def on_ready():
    """Eveniment când botul se conectează"""
    global moderator, rewards_system
    
    logger.info(f"🤖 {bot.user} conectat!")
    
       
    await db_manager.init_database()
    
       
    moderator = ModerationBot(bot)
    
       
    for guild in bot.guilds:
        try:
            await moderator.escalation_system.load_whitelist(str(guild.id))
        except:
            pass
    
       
    try:
        rewards_system = init_rewards_system(bot)
    except:
        logger.warning("⚠️ Sistem recompense indisponibil")
    
    logger.info("✅ Bot pregătit pentru moderare graduală!")

@bot.event
async def on_message(message):
    """Procesează mesajele"""
    if message.author == bot.user or message.author.bot:
        return
    
    if not message.guild:
        return
    
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return
    
    if moderator:
        await moderator.moderate_message(message)

@bot.command(name='test')
async def test_command(ctx):
    
    embed = discord.Embed(
        title="Bot funcțional - Sistem gradual activ!",
        color=discord.Color.green()
    )
    
    embed.add_field(name="🔧 Versiune", value="3.0 - Modular", inline=True)
    embed.add_field(name="🏗️ Arhitectură", value="Moderare toxicitate", inline=True)
    embed.add_field(name="📊 Status", value="🟢 Online", inline=True)
    
       
    systems_status = []
    if moderator:
        systems_status.append("🛡️ Moderare: ✅")
    if moderator and moderator.escalation_system:
        systems_status.append("⚡ Escaladare: ✅")
    if rewards_system:
        systems_status.append("🎁 Recompense: ✅")
    
    embed.add_field(
        name="🔧 Sisteme Active",
        value="\n".join(systems_status) if systems_status else "❌ Niciun sistem",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='analyze')
@commands.has_permissions(manage_messages=True)
async def analyze_text(ctx, *, text: str):
    """Analizează un text"""
    if not moderator:
        await ctx.send("❌ Sistem neinițializat")
        return
    
    result = moderator.analyze_toxicity_level(text)
    
    embed = discord.Embed(
        title="🔍 Rezultat Analiză",
        description=f"Text: `{text[:100]}...`" if len(text) > 100 else f"Text: `{text}`",
        color=discord.Color.red() if result['is_toxic'] else discord.Color.green()
    )
    
    embed.add_field(name="📊 Severitate", value=f"Nivel {result['severity']}/4", inline=True)
    embed.add_field(name="🏷️ Categorie", value=result['level_name'].title(), inline=True)
    embed.add_field(name="⚡ Acțiune", value=result['action'] or "Niciuna", inline=True)
    
    await ctx.send(embed=embed)
    
@bot.command(name='stats')
@commands.has_permissions(manage_messages=True)
async def show_stats(ctx, days: int = 7):
    """Afișează statistici de moderare pentru server"""
    try:
        guild_id = str(ctx.guild.id)
        stats = await db_manager.get_dashboard_stats(guild_id, days)
        
        embed = discord.Embed(
            title=f"📊 Statistici Moderare - Ultimele {days} zile",
            description=f"Raport pentru server **{ctx.guild.name}**",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
           
        total_messages = stats.get('total_messages', 0)
        toxic_messages = stats.get('toxic_messages', 0)
        toxicity_rate = (toxic_messages / max(total_messages, 1)) * 100
        
        embed.add_field(
            name="📈 Activitate Generală",
            value=f"**Mesaje totale:** {total_messages:,}\n"
                  f"**Mesaje toxice:** {toxic_messages:,}\n"
                  f"**Rata toxicitate:** {toxicity_rate:.1f}%",
            inline=False
        )
        
           
        embed.add_field(
            name="⚡ Acțiuni de Moderare",
            value=f"**Avertismente:** {stats.get('warnings', 0):,}\n"
                  f"**Timeout-uri:** {stats.get('timeouts', 0):,}\n"
                  f"**Ban-uri:** {stats.get('bans', 0):,}",
            inline=True
        )
        
           
        positive_messages = stats.get('positive_messages', 0)
        if positive_messages > 0:
            embed.add_field(
                name="🌟 Comportament Pozitiv",
                value=f"**Mesaje pozitive:** {positive_messages:,}\n"
                      f"**Puncte acordate:** {stats.get('total_points', 0):,}\n"
                      f"**Rata pozitivă:** {(positive_messages / max(total_messages, 1)) * 100:.1f}%",
                inline=True
            )
        
        embed.set_footer(text=f"Server: {ctx.guild.name} | Generat la")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"💥 Eroare la afișarea statisticilor: {e}")
        await ctx.send(f"❌ Eroare la obținerea statisticilor: {str(e)}")

@bot.command(name='userinfo')
@commands.has_permissions(manage_messages=True)
async def user_info(ctx, user: discord.Member = None):
    """Afișează informații despre un utilizator și istoricul său"""
    if user is None:
        user = ctx.author
    
    if not moderator:
        await ctx.send("❌ Sistemul de moderare nu este inițializat.")
        return
    
    try:
        guild_id = str(ctx.guild.id)
        user_id = str(user.id)
        
           
        user_stats = await moderator.escalation_system.get_user_stats(user_id, guild_id)
        user_history = await moderator.get_user_history(user_id, guild_id, 5)
        
        embed = discord.Embed(
            title=f"👤 Profil Utilizator: {user.display_name}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
           
        embed.add_field(
            name="📋 Informații de Bază",
            value=f"**Tag:** {user}\n"
                  f"**ID:** `{user.id}`\n"
                  f"**Creat:** {user.created_at.strftime('%d.%m.%Y')}",
            inline=True
        )
        
        embed.add_field(
            name="🏠 În Server",
            value=f"**Intrat:** {user.joined_at.strftime('%d.%m.%Y')}\n"
                  f"**Zile în server:** {(discord.utils.utcnow() - user.joined_at).days}\n"
                  f"**Rol cel mai înalt:** {user.top_role.mention}",
            inline=True
        )
        
           
        embed.add_field(
            name="📊 Statistici Moderare",
            value=f"**Abateri 24h:** {user_stats['violations_24h']}\n"
                  f"**Abateri 7 zile:** {user_stats['violations_7d']}\n"
                  f"**Total abateri:** {user_stats['total_violations']}",
            inline=True
        )
        
           
        if user_history:
            history_text = []
            for entry in user_history[:3]:
                status = "🔴" if entry['is_toxic'] else "🟢"
                history_text.append(f"{status} {entry['category']} ({entry['confidence']:.1%})")
            
            embed.add_field(
                name="📝 Istoric Recent",
                value="\n".join(history_text),
                inline=False
            )
        
           
        if user_stats['violations_24h'] > 0:
            next_level = min(user_stats['violations_24h'] + 1, 6)
            next_action = await moderator.escalation_system.get_action_for_level(next_level)
            
            embed.add_field(
                name="⚡ Status Escaladare",
                value=f"**Nivel curent:** {user_stats['violations_24h']}\n"
                      f"**Următoarea acțiune:** {next_action['action']}\n"
                      f"**Status:** {'🚨 Risc mare' if user_stats['violations_24h'] >= 4 else '⚠️ Sub monitorizare'}",
                inline=True
            )
        else:
            embed.add_field(
                name="✅ Status Escaladare", 
                value="**Fără abateri recente**\nComportament exemplar",
                inline=True
            )
        
        embed.set_footer(text=f"Verificat de {ctx.author}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"💥 Eroare la userinfo: {e}")
        await ctx.send(f"❌ Eroare la obținerea informațiilor: {str(e)}")

@bot.command(name='clearuser')
@commands.has_permissions(administrator=True)
async def clear_user_violations(ctx, user: discord.Member, *, reason: str = "Reset manual"):
    """Șterge toate abaterile unui utilizator din baza de date"""
    
    try:
        guild_id = str(ctx.guild.id)
        user_id = str(user.id)
        
           
        async with await db_manager.get_connection() as db:
               
            cursor = await db.execute("""
                SELECT COUNT(*) FROM moderated_messages 
                WHERE user_id = ? AND guild_id = ? AND is_toxic = 1
            """, (user_id, guild_id))
            
            result = await cursor.fetchone()
            violations_before = result[0] if result else 0
            
            if violations_before == 0:
                await ctx.send(f"ℹ️ {user.mention} nu are abateri în baza de date.")
                return
            
               
            await db.execute("""
                DELETE FROM moderated_messages 
                WHERE user_id = ? AND guild_id = ? AND is_toxic = 1
            """, (user_id, guild_id))
            
            await db.commit()
        
           
        embed = discord.Embed(
            title="🗑️ Utilizator Curățat Complet",
            description=f"Toate abaterile pentru {user.mention} au fost șterse definitiv.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="👤 Utilizator",
            value=f"{user.mention}\n`{user.id}`",
            inline=True
        )
        
        embed.add_field(
            name="👮 Administrator",
            value=f"{ctx.author.mention}\n`{ctx.author.id}`",
            inline=True
        )
        
        embed.add_field(
            name="📋 Motivul",
            value=reason,
            inline=False
        )
        
        embed.add_field(
            name="📊 Abateri Șterse",
            value=f"**{violations_before}** abateri eliminate definitiv",
            inline=True
        )
        
        embed.add_field(
            name="✅ Status Nou",
            value="**Foaie complet curată**\nUtilizator ca și nou",
            inline=True
        )
        
        embed.set_footer(text=f"Reset executat de {ctx.author}")
        
        await ctx.send(embed=embed)
        
        logger.info(f"🗑️ RESET COMPLET pentru {user.display_name}: {violations_before} abateri șterse de către {ctx.author.display_name}")
        
    except Exception as e:
        logger.error(f"💥 Eroare la clearuser: {e}")
        await ctx.send(f"❌ Eroare la resetarea utilizatorului: {str(e)}")



   
async def run_bot():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("❌ Token lipsă!")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"💥 Eroare: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())