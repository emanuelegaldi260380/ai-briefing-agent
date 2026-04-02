# 🤖 AI Briefing Agent

**Il tuo digest quotidiano AI in italiano, consegnato via email ogni mattina.**

Ogni giorno alle 8:00, questo agente:
1. 📡 Raccoglie articoli da 15+ fonti RSS (TechCrunch, OpenAI, Anthropic, DeepMind, ecc.)
2. 🧠 Usa Claude per selezionare le 5 notizie più rilevanti
3. 🇮🇹 Traduce e analizza tutto in italiano con implicazioni pratiche
4. 📧 Ti invia un'email HTML professionale con il briefing

---

## ⚡ Setup Rapido (15 minuti)

### Prerequisiti
- Un account GitHub (gratuito)
- Una API key Anthropic ([console.anthropic.com](https://console.anthropic.com/))
- Un account Gmail (per l'invio email)

### Step 1: Crea l'App Password Gmail

Gmail non accetta la password normale per app esterne. Devi creare una "App Password":

1. Vai su [myaccount.google.com/security](https://myaccount.google.com/security)
2. Attiva la **Verifica in 2 passaggi** (se non l'hai già)
3. Cerca **"Password per le app"** (o vai su [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords))
4. Crea una nuova password per "Mail" → "Altro" → chiama "AI Briefing"
5. **Copia la password di 16 caratteri** (es: `abcd efgh ijkl mnop`)

### Step 2: Crea il Repository GitHub

1. Vai su [github.com/new](https://github.com/new)
2. Nome: `ai-briefing-agent`
3. Seleziona **Private** (consigliato)
4. Clicca "Create repository"

### Step 3: Carica i File

Carica questi file nel repository:
```
ai-briefing-agent/
├── .github/
│   └── workflows/
│       └── daily-briefing.yml
├── ai_briefing_agent.py
├── requirements.txt
└── README.md
```

**Metodo veloce** (da terminale):
```bash
git clone https://github.com/TUO-USERNAME/ai-briefing-agent.git
cd ai-briefing-agent
# Copia qui i file scaricati
git add .
git commit -m "🤖 Setup AI Briefing Agent"
git push
```

**Metodo alternativo** (da browser):
- Vai nel repo su GitHub
- Clicca "Add file" → "Upload files"
- Trascina tutti i file

### Step 4: Configura i Secrets

Questa è la parte più importante — qui inserisci le tue credenziali in modo sicuro:

1. Nel tuo repo GitHub, vai su **Settings** → **Secrets and variables** → **Actions**
2. Clicca **"New repository secret"** e aggiungi questi 4 secrets:

| Nome Secret | Valore | Esempio |
|---|---|---|
| `ANTHROPIC_API_KEY` | La tua API key Anthropic | `sk-ant-api03-xxxxx...` |
| `SMTP_USER` | La tua email Gmail | `mario.rossi@gmail.com` |
| `SMTP_PASSWORD` | L'App Password del Step 1 | `abcd efgh ijkl mnop` |
| `EMAIL_TO` | Email dove ricevere il briefing | `mario.rossi@gmail.com` |

### Step 5: Test!

1. Vai su **Actions** nel tuo repo
2. Clicca su **"🤖 AI Briefing Quotidiano"** nella sidebar
3. Clicca **"Run workflow"** → **"Run workflow"**
4. Attendi 2-3 minuti
5. Controlla la tua email! 📬

Se funziona, il workflow si eseguirà automaticamente ogni mattina alle 8:00 CET.

---

## 🎛️ Personalizzazione

### Modificare le fonti
Apri `ai_briefing_agent.py` e modifica la lista `RSS_FEEDS`. Puoi aggiungere qualsiasi feed RSS.

### Modificare il numero di notizie
Cambia `NUM_TOP_NEWS` nel dizionario `CONFIG` (default: 5).

### Modificare l'orario
Modifica il cron in `.github/workflows/daily-briefing.yml`:
```yaml
cron: "0 7 * * *"    # 7:00 UTC = 8:00 CET
```
Nota: GitHub Actions usa UTC. Per l'ora italiana:
- **Inverno (CET)**: UTC + 1 → per le 8:00 IT, metti `0 7 * * *`
- **Estate (CEST)**: UTC + 2 → per le 8:00 IT, metti `0 6 * * *`

### Usare un altro provider email
Modifica `SMTP_SERVER` e `SMTP_PORT` nel CONFIG o nei secrets:
- **Outlook**: `smtp.office365.com`, porta 587
- **Yahoo**: `smtp.mail.yahoo.com`, porta 587

---

## 💰 Costi

- **GitHub Actions**: Gratuito (2.000 minuti/mese per repo privati)
- **Claude API**: ~$0.01-0.03 per briefing (usa Sonnet, molto economico)
  - Costo mensile stimato: **< $1/mese**
- **Gmail SMTP**: Gratuito

---

## 🐛 Troubleshooting

**L'email non arriva:**
- Controlla la tab "Spam" nella tua email
- Verifica che l'App Password sia corretta (senza spazi extra)
- Controlla i log in GitHub Actions → clicca sul run fallito

**Errore API Anthropic:**
- Verifica che la API key sia attiva su [console.anthropic.com](https://console.anthropic.com/)
- Assicurati di avere credito sufficiente

**Il workflow non parte:**
- GitHub Actions può avere un ritardo fino a 15 minuti sugli schedule
- Verifica che il file YAML sia nella cartella corretta: `.github/workflows/`

---

## 📂 Struttura del Progetto

```
ai-briefing-agent/
├── .github/
│   └── workflows/
│       └── daily-briefing.yml    # Schedulazione GitHub Actions
├── ai_briefing_agent.py          # Script principale dell'agente
├── requirements.txt              # Dipendenze Python
└── README.md                     # Questa guida
```

---

Creato con ❤️ e Claude · [Anthropic](https://www.anthropic.com/)
