#!/usr/bin/env python3
"""
🤖 AI Briefing Agent — Il tuo digest quotidiano AI in italiano
================================================================
Raccoglie notizie da fonti top su AI Generativa, Agentic AI e AI Business,
le analizza e traduce con Claude, e ti invia un briefing email ogni mattina.
"""

import os
import sys
import json
import re
import smtplib
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from typing import Optional

# --- Dipendenze esterne ---
try:
    import feedparser
    import anthropic
    import requests
except ImportError:
    print("Installazione dipendenze...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "feedparser", "anthropic", "requests",
                           "--break-system-packages", "-q"])
    import feedparser
    import anthropic
    import requests


# =============================================================================
# CONFIGURAZIONE — Modifica questi valori o usa variabili d'ambiente
# =============================================================================

CONFIG = {
    # API Anthropic
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),

    # Email - Configurazione SMTP (esempio con Gmail)
    "SMTP_SERVER": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "SMTP_PORT": int(os.environ.get("SMTP_PORT", "587")),
    "SMTP_USER": os.environ.get("SMTP_USER", ""),       # tua-email@gmail.com
    "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""), # App Password Gmail
    "EMAIL_TO": os.environ.get("EMAIL_TO", ""),           # destinatario
    "EMAIL_FROM": os.environ.get("EMAIL_FROM", ""),       # mittente (= SMTP_USER)

    # Parametri agente
    "NUM_TOP_NEWS": 5,           # Numero di notizie nel briefing
    "CLAUDE_MODEL": "claude-sonnet-4-20250514",
    "MAX_ARTICLES_TO_FETCH": 60, # Articoli max da raccogliere prima del filtraggio
}


# =============================================================================
# FONTI RSS — Fonti curate per AI Generativa, Agentic AI, AI Business
# =============================================================================

RSS_FEEDS = [
    # --- AI News Generali ---
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "AI Generativa"
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "AI Generativa"
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "category": "AI Business"
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/feed/",
        "category": "AI Generativa"
    },
    {
        "name": "Ars Technica AI",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "category": "AI Generativa"
    },

    # --- Blog Ufficiali Lab AI ---
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "category": "AI Generativa"
    },
    {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/rss.xml",
        "category": "AI Generativa"
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "category": "AI Generativa"
    },
    {
        "name": "DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "AI Generativa"
    },
    {
        "name": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/rss/",
        "category": "AI Generativa"
    },

    # --- Agentic AI & Developer ---
    {
        "name": "LangChain Blog",
        "url": "https://blog.langchain.dev/rss/",
        "category": "Agentic AI"
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "AI Generativa"
    },

    # --- AI Business ---
    {
        "name": "Harvard Business Review AI",
        "url": "https://hbr.org/topic/ai-and-machine-learning/feed",
        "category": "AI Business"
    },
    {
        "name": "Forbes AI",
        "url": "https://www.forbes.com/ai/feed/",
        "category": "AI Business"
    },

    # --- Ricerca ---
    {
        "name": "arXiv AI (cs.AI)",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "category": "AI Generativa"
    },
]


# =============================================================================
# STEP 1: Raccolta articoli da RSS
# =============================================================================

def fetch_all_articles() -> list[dict]:
    """Raccoglie articoli dalle ultime 24 ore da tutte le fonti RSS."""
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=36)  # 36h per sicurezza

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:10]:  # Max 10 per fonte
                # Parsing data pubblicazione
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                # Se non c'è data, includilo comunque (potrebbe essere recente)
                if pub_date and pub_date < cutoff:
                    continue

                # Estrai sommario/descrizione
                summary = ""
                if hasattr(entry, "summary"):
                    summary = re.sub(r"<[^>]+>", "", entry.summary)[:800]
                elif hasattr(entry, "description"):
                    summary = re.sub(r"<[^>]+>", "", entry.description)[:800]

                article = {
                    "title": entry.get("title", "Senza titolo"),
                    "link": entry.get("link", ""),
                    "summary": summary.strip(),
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                    "pub_date": pub_date.isoformat() if pub_date else "N/A",
                }

                # Deduplica per titolo (hash)
                title_hash = hashlib.md5(article["title"].lower().encode()).hexdigest()
                article["hash"] = title_hash
                articles.append(article)

        except Exception as e:
            print(f"  ⚠️  Errore con {feed_info['name']}: {e}")

    # Rimuovi duplicati
    seen = set()
    unique = []
    for a in articles:
        if a["hash"] not in seen:
            seen.add(a["hash"])
            unique.append(a)

    print(f"📰 Raccolti {len(unique)} articoli unici dalle ultime 36 ore")
    return unique[:CONFIG["MAX_ARTICLES_TO_FETCH"]]


# =============================================================================
# STEP 2: Analisi e selezione con Claude
# =============================================================================

def analyze_and_select(articles: list[dict]) -> str:
    """Usa Claude per selezionare le top 5 notizie e creare il briefing in italiano."""

    client = anthropic.Anthropic(api_key=CONFIG["ANTHROPIC_API_KEY"])

    # Prepara il feed di articoli per Claude
    articles_text = ""
    for i, a in enumerate(articles, 1):
        articles_text += f"""
--- Articolo {i} ---
Titolo: {a['title']}
Fonte: {a['source']}
Categoria: {a['category']}
Link: {a['link']}
Data: {a['pub_date']}
Sommario: {a['summary']}
"""

    today = datetime.now().strftime("%A %d %B %Y")

    prompt = f"""Sei un analista AI esperto. Il tuo compito è creare un briefing quotidiano AI di altissima qualità IN ITALIANO.

DATA DI OGGI: {today}

ISTRUZIONI:
1. Analizza tutti gli articoli qui sotto
2. Seleziona i 5 PIÙ RILEVANTI E IMPATTANTI, privilegiando:
   - Novità su modelli AI (GPT, Claude, Gemini, LLaMA, ecc.)
   - Sviluppi su AI Agentica (agenti autonomi, MCP, workflow, framework)
   - AI applicata al business e all'enterprise
   - Evita notizie vecchie, ripetitive o poco significative
3. Per OGNI notizia selezionata, scrivi IN ITALIANO:
   - Un titolo tradotto e accattivante
   - Un'analisi approfondita di 4-6 righe che spiega COSA è successo e PERCHÉ conta
   - Una sezione "Implicazioni" di 2-3 righe su cosa significa per chi lavora con l'AI
   - Il link originale

FORMATO OUTPUT (segui ESATTAMENTE questo formato JSON):
{{
  "data": "{today}",
  "intro": "Una frase introduttiva di 2 righe che riassuma il tema della giornata AI",
  "notizie": [
    {{
      "numero": 1,
      "titolo_it": "Titolo in italiano",
      "fonte": "Nome fonte",
      "categoria": "AI Generativa | Agentic AI | AI Business",
      "analisi": "Analisi approfondita in italiano...",
      "implicazioni": "Cosa significa per te...",
      "link": "https://..."
    }}
  ]
}}

ARTICOLI DA ANALIZZARE:
{articles_text}

Rispondi SOLO con il JSON valido, senza backtick o altro testo."""

    print("🤖 Claude sta analizzando e selezionando le notizie...")

    response = client.messages.create(
        model=CONFIG["CLAUDE_MODEL"],
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# =============================================================================
# STEP 3: Generazione email HTML
# =============================================================================

def generate_email_html(briefing_json: str) -> tuple[str, str]:
    """Genera un'email HTML professionale dal briefing JSON."""

    # Parsing JSON (con pulizia)
    clean = briefing_json.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\n?", "", clean)
        clean = re.sub(r"\n?```$", "", clean)

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"⚠️  Errore parsing JSON: {e}")
        print(f"Risposta raw:\n{briefing_json[:500]}")
        # Fallback: invia il testo grezzo
        return "🤖 AI Briefing — Errore di parsing", f"<pre>{briefing_json}</pre>"

    today_str = data.get("data", datetime.now().strftime("%d/%m/%Y"))
    intro = data.get("intro", "")
    notizie = data.get("notizie", [])

    subject = f"🤖 AI Briefing — {today_str}"

    # Categoria → emoji mapping
    cat_emoji = {
        "AI Generativa": "🧠",
        "Agentic AI": "🤖",
        "AI Business": "💼",
    }

    # Categoria → colore
    cat_color = {
        "AI Generativa": "#6366f1",
        "Agentic AI": "#10b981",
        "AI Business": "#f59e0b",
    }

    news_html = ""
    for n in notizie:
        cat = n.get("categoria", "AI Generativa")
        emoji = cat_emoji.get(cat, "📰")
        color = cat_color.get(cat, "#6366f1")

        news_html += f"""
        <tr><td style="padding: 0 0 28px 0;">
          <table width="100%" cellpadding="0" cellspacing="0" style="
            background: #ffffff;
            border-radius: 12px;
            border-left: 4px solid {color};
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
          ">
            <tr><td style="padding: 20px 24px;">
              <!-- Badge categoria -->
              <table cellpadding="0" cellspacing="0"><tr>
                <td style="
                  background: {color}15;
                  color: {color};
                  font-size: 11px;
                  font-weight: 600;
                  padding: 4px 10px;
                  border-radius: 20px;
                  letter-spacing: 0.5px;
                  text-transform: uppercase;
                ">{emoji} {cat}</td>
              </tr></table>

              <!-- Titolo -->
              <h2 style="
                margin: 12px 0 8px;
                font-size: 18px;
                font-weight: 700;
                color: #1a1a2e;
                line-height: 1.3;
              ">{n.get('numero', '')}. {n.get('titolo_it', '')}</h2>

              <p style="
                font-size: 11px;
                color: #888;
                margin: 0 0 12px;
              ">Fonte: {n.get('fonte', 'N/A')}</p>

              <!-- Analisi -->
              <p style="
                font-size: 14px;
                color: #333;
                line-height: 1.65;
                margin: 0 0 14px;
              ">{n.get('analisi', '')}</p>

              <!-- Implicazioni -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr><td style="
                  background: #f0fdf4;
                  border-radius: 8px;
                  padding: 12px 16px;
                ">
                  <p style="
                    margin: 0 0 4px;
                    font-size: 12px;
                    font-weight: 700;
                    color: #166534;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                  ">💡 Implicazioni per te</p>
                  <p style="
                    margin: 0;
                    font-size: 13px;
                    color: #15803d;
                    line-height: 1.5;
                  ">{n.get('implicazioni', '')}</p>
                </td></tr>
              </table>

              <!-- Link -->
              <p style="margin: 14px 0 0;">
                <a href="{n.get('link', '#')}" style="
                  color: {color};
                  font-size: 13px;
                  font-weight: 600;
                  text-decoration: none;
                ">Leggi l'articolo originale →</a>
              </p>
            </td></tr>
          </table>
        </td></tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background: #f4f4f8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background: #f4f4f8; padding: 24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%;">

  <!-- Header -->
  <tr><td style="
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px 16px 0 0;
    padding: 32px 28px;
    text-align: center;
  ">
    <h1 style="
      margin: 0 0 6px;
      font-size: 28px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.5px;
    ">🤖 AI Briefing Quotidiano</h1>
    <p style="
      margin: 0;
      font-size: 14px;
      color: #94a3b8;
    ">{today_str} · Le 5 notizie AI che contano</p>
  </td></tr>

  <!-- Intro -->
  <tr><td style="
    background: #1e293b;
    padding: 20px 28px 24px;
  ">
    <p style="
      margin: 0;
      font-size: 14px;
      color: #cbd5e1;
      line-height: 1.6;
      font-style: italic;
    ">{intro}</p>
  </td></tr>

  <!-- Body -->
  <tr><td style="background: #f4f4f8; padding: 28px 16px 8px;">
    <table width="100%" cellpadding="0" cellspacing="0">
      {news_html}
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="
    background: #1a1a2e;
    border-radius: 0 0 16px 16px;
    padding: 20px 28px;
    text-align: center;
  ">
    <p style="margin: 0; font-size: 12px; color: #64748b; line-height: 1.5;">
      Generato automaticamente dal tuo AI Briefing Agent<br>
      Powered by Claude (Anthropic) · Fonti: {len(RSS_FEEDS)} feed RSS curati
    </p>
  </td></tr>

</table>
</td></tr>
</table>

</body>
</html>"""

    return subject, html


# =============================================================================
# STEP 4: Invio email
# =============================================================================

def send_email(subject: str, html_body: str):
    """Invia l'email via SMTP."""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = CONFIG["EMAIL_FROM"] or CONFIG["SMTP_USER"]
    msg["To"] = CONFIG["EMAIL_TO"]

    # Versione plain text di fallback
    plain = re.sub(r"<[^>]+>", "", html_body)
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(CONFIG["SMTP_SERVER"], CONFIG["SMTP_PORT"]) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(CONFIG["SMTP_USER"], CONFIG["SMTP_PASSWORD"])
        server.sendmail(
            CONFIG["EMAIL_FROM"] or CONFIG["SMTP_USER"],
            CONFIG["EMAIL_TO"],
            msg.as_string()
        )

    print(f"✅ Email inviata a {CONFIG['EMAIL_TO']}")


# =============================================================================
# STEP 5 (Opzionale): Salva anche una copia locale HTML
# =============================================================================

def save_local_copy(subject: str, html_body: str):
    """Salva una copia locale del briefing."""
    os.makedirs("archive", exist_ok=True)
    filename = f"archive/briefing_{datetime.now().strftime('%Y-%m-%d')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_body)
    print(f"💾 Copia salvata in: {filename}")


# =============================================================================
# MAIN — Orchestrazione pipeline
# =============================================================================

def main():
    print("=" * 60)
    print(f"🤖 AI BRIEFING AGENT — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)

    # Validazione configurazione
    missing = []
    for key in ["ANTHROPIC_API_KEY", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO"]:
        if not CONFIG[key]:
            missing.append(key)

    if missing:
        print(f"\n❌ Variabili mancanti: {', '.join(missing)}")
        print("Configurale come variabili d'ambiente o nel file CONFIG.")
        sys.exit(1)

    # Pipeline
    print("\n📡 Step 1: Raccolta articoli dai feed RSS...")
    articles = fetch_all_articles()

    if not articles:
        print("⚠️  Nessun articolo trovato. Controlla la connessione internet.")
        sys.exit(1)

    print(f"\n🧠 Step 2: Analisi con Claude ({CONFIG['CLAUDE_MODEL']})...")
    briefing_json = analyze_and_select(articles)

    print("\n🎨 Step 3: Generazione email HTML...")
    subject, html_body = generate_email_html(briefing_json)

    print("\n📧 Step 4: Invio email...")
    try:
        send_email(subject, html_body)
    except Exception as e:
        print(f"❌ Errore invio email: {e}")
        print("   Salvo copia locale come fallback...")

    save_local_copy(subject, html_body)

    print("\n✅ Briefing completato con successo!")
    print("=" * 60)


if __name__ == "__main__":
    main()
