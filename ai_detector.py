
import logging
import re
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass
import json

@dataclass
class MessageAnalysis:
    """Rezultatul analizei unui mesaj"""
    is_toxic: bool
    toxicity_score: float
    sentiment: str  
    sentiment_score: float
    confidence: float
    method_used: str
    recommended_action: str
    category: str = "general"
    severity: str = "low"

class AIDetector:
    """AI Detector cu dual model - Toxicitate + Sentiment ÎMBUNĂTĂȚIT"""
    
    def __init__(self, educational_config: dict = None):
        self.logger = logging.getLogger(__name__)
        self.educational_config = educational_config or self._load_educational_config()
        
        self.toxicity_model = None
        self.sentiment_model = None
        
        self.toxic_patterns = {
               
            r'\b(prost|proast[aă]|idiot|idioat[aă]|cretin|imbecil|tâmpit|dobitoc)\b': 0.9,
            r'\b(prost.*de.*tine|esti.*prost)\b': 0.95,
            
               
            r'\b(dracu|naiba|mortii|morții|pizd|fut|cur|căca|rahat)\b': 0.8,
            r'\b(plm|pula|coaie|muie)\b': 0.95,
            
               
            r'\b(omor|ucid|bat|distrug|termin|tai|sparg)\b': 0.95,
            r'\b(mor[iî]|crăp[aă]|să.*mor[iî])\b': 0.9,
            
               
            r'\b(urât|urâ[tț][aă]|scârbos|dezgustător|oribil|groaznic)\b': 0.7,
            
               
            r'\b(retardat|handicapat|prost.*naibii|idiot.*dracu)\b': 0.95,
        }
        
        self.positive_patterns = {
               
            r'\b(mulțumesc|mulțumiri|mersi|ms|thanks|thank you)\b': 0.9,
            r'\b(apreciez|respect|recunosc)\b': 0.85,
            
               
            r'\b(bravo|felicitări|excelent|minunat|grozav|super|tare)\b': 0.8,
            r'\b(bun[aă].*treab[aă]|foarte.*bine)\b': 0.85,
            
               
            r'\b(ajut|colabor|împreun[aă]|susțin|sprijin)\b': 0.75,
            r'\b(să.*ajut|pot.*ajuta|cum.*pot.*ajuta)\b': 0.9,
            
               
            r'\b(vă.*rog|te.*rog|scuze|scuz[aă]|îmi.*pare.*rău)\b': 0.8,
            r'\b(bun[aă].*ziua|salut|bun[aă])\b': 0.6,
        }
        
        self._load_models()
    
    def _load_educational_config(self):
        try:
            with open('educational_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Nu s-a putut încărca educational_config.json: {e}")
            return {}
    
    def _load_models(self):
        try:
            from transformers import pipeline
            
               
            self.logger.info("🔥 Încărcare model toxicitate...")
            try:
                self.toxicity_model = pipeline(
                    "text-classification",
                    model="martin-ha/toxic-comment-model",
                    device=-1,
                    truncation=True,
                    max_length=512
                )
                self.logger.info("✅ Model toxicitate încărcat!")
            except Exception as e:
                self.logger.error(f"❌ Eroare model toxicitate: {e}")
                self.toxicity_model = None
            
               
            self.logger.info("😊 Încărcare model sentiment...")  
            try:
                self.sentiment_model = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=-1,
                    truncation=True,
                    max_length=512
                )
                self.logger.info("✅ Model sentiment încărcat!")
            except Exception as e:
                self.logger.warning(f"⚠️ Eroare model sentiment: {e}")
                self.sentiment_model = None
                    
        except ImportError:
            self.logger.error("❌ Transformers nu este disponibil!")
            self.toxicity_model = None
            self.sentiment_model = None
    
    def predict_toxicity(self, text: str) -> tuple[bool, float, str]:
        analysis = self.analyze_message(text)
        return analysis.is_toxic, analysis.toxicity_score, analysis.method_used
    
    def analyze_message(self, text: str) -> MessageAnalysis:
        
        text_normalized = self._normalize_text(text)
        
        is_toxic, toxicity_score, toxic_category = self._detect_toxicity_advanced(text, text_normalized)
        
        sentiment, sentiment_score = self._detect_sentiment_advanced(text, text_normalized)
        
        if sentiment == "POSITIVE" and toxicity_score < 0.5:
            toxicity_score *= 0.7
            is_toxic = toxicity_score >= 0.5
        
        confidence = max(toxicity_score, sentiment_score) if toxicity_score > 0 else sentiment_score
        method_used = "ai_model" if (self.toxicity_model or self.sentiment_model) else "patterns"
        
        severity = self._determine_severity(toxicity_score, toxic_category)
        
        action = self._determine_action(is_toxic, toxicity_score, sentiment, sentiment_score, severity)
        
        return MessageAnalysis(
            is_toxic=is_toxic,
            toxicity_score=toxicity_score,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            confidence=confidence,
            method_used=method_used,
            recommended_action=action,
            category=toxic_category if is_toxic else "neutral",
            severity=severity
        )
    
    def _normalize_text(self, text: str) -> str:        
        text = text.lower()
        
        replacements = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
            'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        return text
    
    def _detect_toxicity_advanced(self, text: str, text_normalized: str) -> Tuple[bool, float, str]:
        """Detectare avansată de toxicitate"""
        max_score = 0.0
        detected_category = "general"
        pattern_found = False
        
        for pattern, score in self.toxic_patterns.items():
            if re.search(pattern, text_normalized, re.IGNORECASE):
                if score > max_score:
                    max_score = score
                    pattern_found = True
                    if 'prost' in pattern or 'idiot' in pattern:
                        detected_category = "harassment"
                    elif 'omor' in pattern or 'bat' in pattern or 'ucid' in pattern:
                        detected_category = "threats"
                    elif 'dracu' in pattern or 'pizd' in pattern:
                        detected_category = "profanity"
                    else:
                        detected_category = "toxicity"
        
        bypass_patterns = [
            (r'p\s*r\s*o\s*s\s*t', 0.85),     
            (r'pr0st|pro\$t|pr@st', 0.85),     
            (r'🖕|🤬', 0.8),     
            
            (r'\b(te.*omor|te.*ucid|te.*bat|te.*distrug|te.*termin)\b', 0.95),
            (r'\b(o.*sa.*mori|vei.*muri|sa.*mori)\b', 0.92),
            (r'\b(iti.*rup|iti.*sparg|iti.*fac)\b', 0.88),
        ]
        
        for pattern, score in bypass_patterns:
            if re.search(pattern, text_normalized, re.IGNORECASE):
                if score > max_score:
                    max_score = score
                    pattern_found = True
                    if 'omor' in pattern or 'ucid' in pattern or 'mori' in pattern:
                        detected_category = "threats"
                    else:
                        detected_category = "harassment"
        
        
        ai_score = 0.0
        if self.toxicity_model:
            try:
                results = self.toxicity_model(text)
                
                
                if isinstance(results, list) and len(results) > 0:
                    result = results[0]
                    
                    
                    if result['label'] == 'TOXIC':
                        ai_score = result['score']
                        self.logger.debug(f"AI detectează TOXIC cu score: {ai_score}")
                    elif result['label'] == 'NON-TOXIC':
                        ai_score = 1.0 - result['score']  
                        self.logger.debug(f"AI detectează NON-TOXIC cu score: {result['score']} → toxicity: {ai_score}")
                            
            except Exception as e:
                self.logger.debug(f"Eroare model toxicitate: {e}")
        
        final_score = max_score
        
        if ai_score > 0:
            if pattern_found:
                if max_score >= 0.8:  
                       
                    final_score = max(max_score, ai_score * 0.7)
                elif max_score >= 0.5:     
                       
                    final_score = (max_score * 0.7 + ai_score * 0.3)
                else:     
                       
                    final_score = max(max_score, ai_score * 0.8)
            else:
                   
                if ai_score >= 0.7:
                    final_score = ai_score * 0.75     
                else:
                    final_score = ai_score * 0.6      
        
           
        threat_indicators = ['omor', 'ucid', 'bat', 'distrug', 'termin', 'mori', 'rup', 'sparg']
        if any(word in text_normalized for word in threat_indicators):
            if final_score < 0.7:     
                final_score = max(final_score, 0.8)
                detected_category = "threats"
                self.logger.debug(f"Forțat scor amenințare: {final_score}")
        
        is_toxic = final_score >= 0.5
        self.logger.debug(f"Toxicitate finală - Pattern: {max_score}, AI: {ai_score}, Final: {final_score}, Categorie: {detected_category}")
        
        return is_toxic, final_score, detected_category

    def _detect_sentiment_advanced(self, text: str, text_normalized: str) -> Tuple[str, float]:
        """Detectare avansată de sentiment"""
        pos_score = 0.0
        neg_score = 0.0
        pattern_pos_found = False
        pattern_neg_found = False
        
           
        for pattern, score in self.positive_patterns.items():
            if re.search(pattern, text_normalized, re.IGNORECASE):
                pos_score = max(pos_score, score)
                pattern_pos_found = True
                self.logger.debug(f"Pattern pozitiv găsit: {pattern} → Score: {score}")
        
           
        negative_patterns = {
            r'\b(nu.*place|nu.*bun|rau|gresit|prost.*facut)\b': 0.6,
            r'\b(dezamagit|trist|suparat|nervos)\b': 0.7,
            r'\b(plictisitor|boring|nasol)\b': 0.6,
            r'\b(nu.*imi.*pasa|nu.*ma.*intereseaza)\b': 0.8,
        }
        
        for pattern, score in negative_patterns.items():
            if re.search(pattern, text_normalized, re.IGNORECASE):
                neg_score = max(neg_score, score)
                pattern_neg_found = True
                self.logger.debug(f"Pattern negativ găsit: {pattern} → Score: {score}")
        
       
        intensifier_patterns = {
            r'foarte.*mult.*multumesc|multumesc.*din.*suflet': 0.99,
            r'multumesc.*foarte.*mult|foarte.*recunoscator': 0.95,
            r'sa.*lucram.*impreuna|hai.*sa.*colaboram': 0.95,
            r'cum.*pot.*sa.*te.*ajut|pot.*sa.*ajut': 0.9,
            r'apreciez.*foarte.*mult|respect.*foarte.*mult': 0.9,
            r'esti.*foarte.*de.*ajutor|foarte.*util': 0.85,
               
            r'\b(colabor.*impreuna|lucr.*impreuna|sa.*colabor)\b': 0.9,
            r'\b(sa.*rezolv.*impreuna|sa.*facem.*impreuna)\b': 0.88,
        }
        
        for pattern, score in intensifier_patterns.items():
            if re.search(pattern, text_normalized, re.IGNORECASE):
                pos_score = max(pos_score, score)
                pattern_pos_found = True
                self.logger.debug(f"Intensificator pozitiv găsit: {pattern} → Score: {score}")
        
           
        positive_word_count = 0
        positive_words = ['multumesc', 'apreciez', 'colabor', 'ajut', 'respect', 'grozav', 'excelent', 'bun', 'foarte', 'impreuna']
        
        for word in positive_words:
            if word in text_normalized:
                positive_word_count += 1
        
           
        if positive_word_count >= 2:
            bonus = min(0.3, positive_word_count * 0.1)
            pos_score = min(1.0, pos_score + bonus)
            pattern_pos_found = True
            self.logger.debug(f"Bonus cuvinte pozitive: +{bonus} (găsite {positive_word_count})")
        
           
        ai_pos_score = 0.0
        ai_neg_score = 0.0
        ai_confidence = 0.0
        
        if self.sentiment_model:
            try:
                results = self.sentiment_model(text)
                
                if isinstance(results, list) and len(results) > 0:
                       
                    best_result = max(results, key=lambda x: x['score'])
                    label = best_result['label'].upper()
                    ai_confidence = best_result['score']
                    
                    self.logger.debug(f"AI Sentiment: {label} cu score {ai_confidence}")
                    
                       
                    if 'POS' in label or 'POSITIVE' in label:
                        ai_pos_score = ai_confidence
                    elif 'NEG' in label or 'NEGATIVE' in label:
                        ai_neg_score = ai_confidence
                        
            except Exception as e:
                self.logger.debug(f"Eroare model sentiment: {e}")
        
           
        final_pos_score = pos_score
        final_neg_score = neg_score
        
        if ai_confidence > 0:
            if pattern_pos_found and ai_pos_score > 0:
                   
                final_pos_score = max(pos_score, ai_pos_score * 0.95)
            elif pattern_pos_found and ai_pos_score == 0:
                   
                final_pos_score = max(pos_score, 0.7)
            elif not pattern_pos_found and ai_pos_score > 0:
                   
                final_pos_score = ai_pos_score * 0.8
                
            if pattern_neg_found and ai_neg_score > 0:
                   
                final_neg_score = max(neg_score, ai_neg_score * 0.9)
            elif pattern_neg_found and ai_neg_score == 0:
                   
                final_neg_score = max(neg_score, 0.6)
            elif not pattern_neg_found and ai_neg_score > 0:
                   
                final_neg_score = ai_neg_score * 0.8
        
           
        collaboration_keywords = ['colabor', 'impreuna', 'lucr.*impreuna', 'sa.*rezolv', 'sa.*facem']
        if any(re.search(keyword, text_normalized) for keyword in collaboration_keywords):
            if final_pos_score < 0.7:
                final_pos_score = max(final_pos_score, 0.8)
                self.logger.debug(f"Forțat pozitiv pentru colaborare: {final_pos_score}")
        
        self.logger.debug(f"Scoruri finale - Pozitiv: {final_pos_score}, Negativ: {final_neg_score}")
        
           
        if final_pos_score > final_neg_score and final_pos_score >= 0.4:
            return "POSITIVE", final_pos_score
        elif final_neg_score > final_pos_score and final_neg_score >= 0.5:
            return "NEGATIVE", final_neg_score
        else:
               
            neutral_score = max(final_pos_score, final_neg_score) if final_pos_score > 0 or final_neg_score > 0 else 0.3
            return "NEUTRAL", neutral_score

    def detect_positive_sentiment(self, message: str) -> tuple[bool, int]:
        """Compatibilitate cu RewardsSystem - ÎMBUNĂTĂȚITĂ"""
        analysis = self.analyze_message(message)
        
           
        self.logger.debug(f"Analiză mesaj: '{message}'")
        self.logger.debug(f"Sentiment detectat: {analysis.sentiment} cu score {analysis.sentiment_score}")
        
           
        is_positive = False
        
        if analysis.sentiment == "POSITIVE":
               
            is_positive = analysis.sentiment_score >= 0.4
        elif analysis.sentiment == "NEUTRAL":
               
            message_lower = message.lower()
            
               
            collaboration_indicators = [
                'să colaborăm', 'colabor', 'împreună', 'să lucrăm', 
                'să rezolvăm', 'să facem', 'cum pot să ajut'
            ]
            
               
            positive_indicators = [
                'mulțumesc', 'mulțumiri', 'apreciez', 'respect', 
                'ajut', 'grozav', 'excelent', 'bravo'
            ]
            
               
            all_indicators = collaboration_indicators + positive_indicators
            
            if any(indicator in message_lower for indicator in all_indicators):
                is_positive = True
                   
                analysis.sentiment_score = max(analysis.sentiment_score, 0.8)
                self.logger.debug(f"Forțat pozitiv din cauza indicatorilor: {analysis.sentiment_score}")
        
           
        score_int = max(1, min(10, int(analysis.sentiment_score * 10)))
        
           
        if is_positive and score_int < 4:
            score_int = 6
        
        self.logger.debug(f"Rezultat final: is_positive={is_positive}, score_int={score_int}")
        
        return is_positive, score_int

    def _determine_severity(self, toxicity_score: float, category: str) -> str:
        if category in ["threats", "hate_speech"] or toxicity_score >= 0.9:
            return "high"
        elif toxicity_score >= 0.7:
            return "medium"
        else:
            return "low"

    def _determine_action(self, is_toxic: bool, toxicity_score: float, 
                        sentiment: str, sentiment_score: float, severity: str) -> str:
        """Determină acțiunea recomandată"""
        if not is_toxic:
            if sentiment == "POSITIVE" and sentiment_score >= 0.6:
                return "REWARD"
            else:
                return "IGNORE"
        else:
            if severity == "high" or toxicity_score >= 0.85:
                return "SEVERE_PENALTY"
            elif severity == "medium" or toxicity_score >= 0.65:
                return "MODERATE_PENALTY"
            else:
                return "LIGHT_PENALTY"
    
    def detect_positive_sentiment(self, message: str) -> tuple[bool, int]:
        """Compatibilitate cu RewardsSystem - ÎMBUNĂTĂȚITĂ"""
        analysis = self.analyze_message(message)
        
           
        self.logger.debug(f"Analiză mesaj: '{message}'")
        self.logger.debug(f"Sentiment detectat: {analysis.sentiment} cu score {analysis.sentiment_score}")
        
           
        is_positive = False
        
        if analysis.sentiment == "POSITIVE":
               
            is_positive = analysis.sentiment_score >= 0.4     
        elif analysis.sentiment == "NEUTRAL":
               
               
            message_lower = message.lower()
            strong_positive_indicators = [
                'mulțumesc', 'mulțumiri', 'apreciez', 'respect', 
                'colabor', 'ajut', 'grozav', 'excelent', 'bravo'
            ]
            
            if any(indicator in message_lower for indicator in strong_positive_indicators):
                is_positive = True
                   
                analysis.sentiment_score = max(analysis.sentiment_score, 0.7)
                self.logger.debug(f"Forțat pozitiv din cauza indicatorilor: {analysis.sentiment_score}")
        
           
        score_int = max(1, min(10, int(analysis.sentiment_score * 10)))
        
           
        if is_positive and score_int < 4:
            score_int = 6
        
        self.logger.debug(f"Rezultat final: is_positive={is_positive}, score_int={score_int}")
        
        return is_positive, score_int

   
_global_detector = None

def get_detector():
    """Obține instanța globală"""
    global _global_detector
    if _global_detector is None:
        _global_detector = AIDetector()
    return _global_detector

async def analyze_message(text: str, user_history: list = None) -> dict:
    """Funcție simplă pentru compatibilitate"""
    detector = get_detector()
    analysis = detector.analyze_message(text)
    
    return {
        'is_toxic': analysis.is_toxic,
        'toxicity_score': analysis.toxicity_score,
        'sentiment': analysis.sentiment,
        'sentiment_score': analysis.sentiment_score,
        'confidence': analysis.confidence,
        'method': analysis.method_used,
        'action': analysis.recommended_action,
        'category': analysis.category,
        'severity': analysis.severity,
        'scores': {
            'overall_toxicity': analysis.toxicity_score,
            'sentiment': analysis.sentiment_score,
            'confidence': analysis.confidence
        }
    }

async def analyze_message_complete(text: str, user_history: list = None, config: dict = None) -> dict:
    """Funcție completă pentru discord_bot.py"""
    base_analysis = await analyze_message(text, user_history)
    
       
    base_analysis['educational_feedback'] = {
        'main_message': "Mesajul tău conține limbaj care poate deranja alți membri.",
        'explanation': "O comunicare respectuoasă face comunitatea mai plăcută pentru toți.",
        'suggestions': [
            "Exprimă-ți opinia fără limbaj ofensator",
            "Folosește critici constructive",
            "Gândește-te la impactul cuvintelor tale"
        ],
        'strategy_used': 'educational_approach',
        'severity': base_analysis.get('severity', 'low')
    }
    
       
    action_map = {
        'LIGHT_PENALTY': 'warning',
        'MODERATE_PENALTY': 'mute', 
        'SEVERE_PENALTY': 'ban',     
        'REWARD': 'reward',
        'IGNORE': 'none'
    }
    
       
    if base_analysis['is_toxic']:
        if base_analysis['toxicity_score'] >= 0.9:
            base_analysis['action'] = 'ban'
        elif base_analysis['toxicity_score'] >= 0.7:
            base_analysis['action'] = 'mute'
        else:
            base_analysis['action'] = 'warning'
    else:
        base_analysis['action'] = action_map.get(base_analysis['action'], 'none')
    
    return base_analysis

class ToxicityDetector:
    """Clasă pentru compatibilitate"""
    def __init__(self):
        self.model = None
        self.detector = AIDetector()
    
    async def load_model(self):
        """Încarcă modelul (pentru compatibilitate)"""
        self.model = True
    
    async def predict_toxicity(self, text: str) -> tuple:
        """Funcție de compatibilitate"""
        return self.detector.predict_toxicity(text)

   
toxicity_detector = ToxicityDetector()