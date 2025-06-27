
#  README – Discord AI Moderation Bot

##  Descrierea Livrabilelor

Acest repository conține **întregul cod sursă** pentru un bot Discord inteligent de moderare, construit în scop educațional. Proiectul utilizează modele AI pre-antrenate pentru detectarea toxicității și analiza sentimentului mesajelor din chat. Accentul este pus pe **feedback educațional**, **moderare progresivă**, și **gamificarea comportamentului pozitiv**.

###  Adresa Git Repository
> `https://github.com/corinabistrita/botdiscord-antitoxicity`  



---

## Pași de Compilare și Instalare

### 1. Clonarea repository-ului:
```bash
git clone https://github.com/corinabistrita/botdiscord-antitoxicity
cd discord-ai-moderation-bot
```

### 2. Crearea unui mediu virtual Python:
```bash
# Windows
python -m venv bot_env
bot_env\Scripts\activate

# Linux/Mac
python3 -m venv bot_env
source bot_env/bin/activate
```

### 3. Instalarea dependențelor:
```bash
pip install -r requirements.txt
```

---

##  Pași de Lansare a Aplicației

### 1. Configurare `.env`
```bash
cp .env.example .env
# Editează tokenul Discord în .env
```

### 2. Pornirea aplicației:
```bash
python run.py
```

### 3. Accesarea dashboard-ului:
- http://localhost:8000 – aplicație web
- http://localhost:8000/docs – API interactiv FastAPI

---

##  Structura Proiectului

```
discord-ai-moderation-bot/
├── ai_detector.py
├── api.py
├── database.py
├── discord_bot.py
├── escalation_system.py
├── rewards_system.py
├── run.py
├── test_system.py
├── educational_config.json
├── requirements.txt
├── .env.example
├── README.md
├── dashboard/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── logs/
```
 Livrabile – Conținutul proiectului

ai_detector.py – Conține logica de analiză AI. Folosește modele pre-antrenate pentru a detecta toxicitatea și sentimentul unui mesaj.

discord_bot.py – Codul principal al botului Discord. Ascultă mesajele, apelează detectorul AI și răspunde cu acțiuni (ex: avertismente).

escalation_system.py – Decide ce sancțiune se aplică (ex: avertisment, timeout, ban) în funcție de istoricul utilizatorului.

rewards_system.py – Detectează comportamentul pozitiv și oferă recompense (puncte, roluri, etc).

api.py – Server FastAPI care oferă API-uri REST. Permite interacțiunea cu dashboard-ul web (statistici, configurare).

dashboard/index.html – Pagina principală a dashboard-ului web, unde administratorii pot vedea și configura botul.

dashboard/style.css – Stilurile vizuale pentru dashboard-ul web.

dashboard/script.js – Scripturile JavaScript care adaugă interactivitate dashboard-ului (ex: grafice, comenzi API).

educational_config.json – Configurații pentru mesaje educaționale (ex: textul avertismentelor, sugestii).

test_system.py – Script de testare a componentelor sistemului (AI, DB, API etc).

run.py – Script principal de pornire a aplicației. Inițializează botul, API-ul și celelalte componente.

requirements.txt – Lista cu toate pachetele Python necesare pentru rularea aplicației (ex: discord.py, transformers etc).

##  Testare Sistem

### Test complet:
```bash
python test_system.py
```

### Test rapid AI:
```bash
python test_system.py quick
```

##  Securitate și Logging

- Rate limiting API
- Logs în directorul `logs/`
- Audit trail pentru acțiuni administrative



