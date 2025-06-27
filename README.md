
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

## 🛠️ Testare Sistem

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



