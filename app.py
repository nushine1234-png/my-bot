import streamlit as st
import requests
from google import genai
import os
import re
import csv
import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Nova - Nu Shine Dental Assistant",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }
.main { background: #f8fafc; }
.stApp { background: #f8fafc; }
header { background: transparent !important; }
.stChatMessage { background: white; border-radius: 12px; padding: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-bottom: 8px; color: #1e293b; font-size: 0.9rem; }
.stChatMessage[data-testid="stChatMessage"]:nth-child(odd) { background: #f1f5f9; }
.stChatMessage p, .stChatMessage div, .stChatMessage span, .stChatMessage li { color: #1e293b !important; }
.stChatMessage strong { color: #1E3A8A !important; }
.chat-title { text-align: center; padding: 20px 16px 10px; background: linear-gradient(135deg, #1E3A8A 0%, #1a5a9e 100%); border-radius: 0 0 24px 24px; color: white; }
.chat-title h1 { font-size: 1.6rem; font-weight: 800; margin: 0; }
.chat-title p { font-size: 0.8rem; opacity: 0.8; margin: 4px 0 0; }
.chat-title .badge { display: inline-block; background: rgba(255,255,255,0.15); padding: 2px 12px; border-radius: 50px; font-size: 0.65rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
.feature-badges { display: flex; justify-content: center; gap: 6px; flex-wrap: wrap; margin: 4px 0 8px; }
.feature-badges span { background: #e2e8f0; padding: 2px 10px; border-radius: 50px; font-size: 0.68rem; color: #475569; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }
.stChatInputContainer { position: sticky !important; bottom: 0 !important; background: white !important; padding: 8px 12px !important; border-top: 1px solid #e2e8f0 !important; }
[data-testid="stChatInput"] input { autocorrect: off; -webkit-autocorrect: off; }
footer { display: none !important; }
#MainMenu { display: none !important; }
.stAppDeployButton { display: none !important; }
</style>
""", unsafe_allow_html=True)

API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY", "YOUR_OPENWEATHER_API_KEY")

client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = (
    "You are Nova, a friendly virtual receptionist for Nu Shine Dental. "
    "CRITICAL: Keep every reply to 2-3 short sentences maximum. Never write paragraphs or long blocks of text. "
    "Be warm, simple, and conversational. No medical jargon. "
    "After answering briefly, gently ask for their name and phone number to book a visit. "
    "Mention our 'team of expert doctors' naturally if relevant. "
    "Don't make up clinic addresses or timings — say the team will call them back. "
    "Never diagnose or prescribe. Always advise an in-person consultation."
)

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patient_leads.csv")

def extract_lead(text):
    phone = None
    m = re.search(r'\b(\d{10})\b', text)
    if m:
        phone = m.group(1)
    return phone

def save_lead(user_text):
    phone = extract_lead(user_text)
    if not phone:
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Phone", "Message"])
        writer.writerow([now, phone, user_text.replace("\n", " ")])
    return True

BRANCHES = ["eluru", "guntur", "tanuku", "nidadavolu", "palakol", "kondapalli"]
TREATMENTS = [
    "root canal", "rct", "crown", "bridge", "implant", "dental implant",
    "smile design", "smile designing", "braces", "aligner", "teeth whitening",
    "whitening", "cleaning", "scaling", "pediatric", "child", "kids",
    "extraction", "removal", "filling", "filling", "dentures", "gum",
    "periodontitis", "pyorrhoea", "sensitive", "pain", "toothache",
    "cosmetic", "veneers", "laminate", "rehabilitation", "mouth rehabilitation",
    "night guard", "retainer", "x-ray", "xray", "radiograph"
]
TIME_KEYWORDS = ["morning", "afternoon", "evening", "night", "today", "tomorrow",
                 "asap", "urgent", "emergency", "this week", "next week"]

def extract_lead_details(text):
    details = {"name": "", "concern": "", "branch_time": ""}
    t = text.strip()

    name_patterns = [
        r"(?:my\s+name\s+is|i['’]?m|i\s+am|this\s+is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        r"^([A-Za-z]+(?:\s+[A-Za-z]+)?)[,.\s]"
    ]
    for pat in name_patterns:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            details["name"] = m.group(1).strip().title()
            break

    lower = t.lower()
    found_treatments = []
    for tr in TREATMENTS:
        if tr in lower:
            found_treatments.append(tr.title())
    if found_treatments:
        details["concern"] = ", ".join(sorted(set(found_treatments), key=lambda x: found_treatments.index(x)))

    parts = []
    for b in BRANCHES:
        if b in lower:
            parts.append(b.title())
    for tk in TIME_KEYWORDS:
        if tk in lower:
            parts.append(tk.title())
    if parts:
        details["branch_time"] = ", ".join(parts)

    return details

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

def send_webhook(payload):
    if not WEBHOOK_URL or "your_" in WEBHOOK_URL.lower() or WEBHOOK_URL.count("/") < 4:
        return
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception:
        pass

def get_secret(key, default=""):
    for k in (key, key.upper(), key.lower()):
        try:
            return st.secrets[k]
        except (FileNotFoundError, KeyError):
            pass
    return os.getenv(key, os.getenv(key.upper(), default))

def init_gsheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        raw = get_secret("gcp_service_account", "")
        if not raw or raw in ("{}", "your_service_account_json_here", ""):
            st.error("❌ Google Sheets: GCP_SERVICE_ACCOUNT secret is missing or placeholder")
            return None

        if isinstance(raw, str):
            try:
                creds_dict = json.loads(raw)
            except json.JSONDecodeError as e:
                st.error(f"❌ Google Sheets: GCP_SERVICE_ACCOUNT is not valid JSON — {e}")
                return None
            if not isinstance(creds_dict, dict):
                st.error(f"❌ Google Sheets: JSON parsed as {type(creds_dict).__name__}, expected dict")
                return None
        elif isinstance(raw, dict):
            creds_dict = raw
        elif isinstance(raw, list):
            st.error("❌ Google Sheets: GCP_SERVICE_ACCOUNT is a list — in secrets, wrap with triple quotes '''{...}'''")
            return None
        else:
            st.error(f"❌ Google Sheets: Unexpected type {type(raw).__name__} for GCP_SERVICE_ACCOUNT")
            return None

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        sheet_id = get_secret("gsheet_id", "")
        if not sheet_id:
            st.error("❌ Google Sheets: GSHEET_ID not found in secrets")
            return None

        sheet = client.open_by_key(sheet_id).sheet1
        if sheet.row_count == 0:
            sheet.append_row(["Timestamp", "Name", "Phone", "Concern", "Branch/Time", "Raw Message"])
        st.success("✅ Google Sheets connected successfully")
        return sheet
    except Exception as e:
        st.error(f"❌ Google Sheets init failed: {type(e).__name__}: {e}")
        return None

def append_to_gsheet(sheet, lead_data):
    if sheet is None:
        return False
    try:
        sheet.append_row([
            lead_data["timestamp"],
            lead_data["name"],
            lead_data["phone"],
            lead_data["concern"],
            lead_data["branch_time"],
            lead_data["raw_message"]
        ])
        return True
    except Exception as e:
        st.error(f"❌ Google Sheets append failed: {type(e).__name__}: {e}")
        return False

def send_email_alert(lead_data):
    smtp_server = get_secret("email_smtp_server", "smtp.gmail.com")
    smtp_port = int(get_secret("email_smtp_port", "587"))
    sender = get_secret("email_sender", "")
    password = get_secret("email_password", "")
    recipient = get_secret("email_recipient", "")

    missing = []
    if not smtp_server: missing.append("EMAIL_SMTP_SERVER")
    if not sender: missing.append("EMAIL_SENDER")
    if not password: missing.append("EMAIL_PASSWORD")
    if not recipient: missing.append("EMAIL_RECIPIENT")
    if missing:
        st.warning(f"⚠️ Email not configured — secrets not found: {', '.join(missing)}")
        return False

    try:
        subject = f"🚨 New Lead - {lead_data['name'] or 'Unknown'}"
        body = (
            f"🚨 New Appointment Request 🚨\n\n"
            f"Name: {lead_data['name'] or 'Not provided'}\n"
            f"Phone: {lead_data['phone']}\n"
            f"Concern: {lead_data['concern'] or 'Not specified'}\n"
            f"Branch/Time: {lead_data['branch_time'] or 'Not specified'}\n"
            f"Message: {lead_data['raw_message']}\n"
            f"Timestamp: {lead_data['timestamp']}"
        )
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        st.info(f"📧 Connecting to {smtp_server}:{smtp_port} as {sender} → {recipient}")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        st.success("✅ Email alert sent to clinic")
        return True
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Email auth failed — use Gmail App Password (not regular password). Generate at https://myaccount.google.com/apppasswords")
        return False
    except smtplib.SMTPException as e:
        st.error(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Email send failed: {type(e).__name__}: {e}")
        return False

if "gsheet" not in st.session_state:
    st.session_state.gsheet = init_gsheet()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<div class="chat-title"><div class="badge">🦷 NU SHINE DENTAL</div><h1>Nova</h1><p>How can I help you with your dental care today?</p></div>', unsafe_allow_html=True)
st.markdown('<div class="feature-badges"><span>🦷 Dental Queries</span><span>📅 Appointment Booking</span><span>💬 Ask Nova</span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.markdown('</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Tell Nova your dental concern..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if save_lead(prompt):
        details = extract_lead_details(prompt)
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phone": extract_lead(prompt),
            "name": details["name"],
            "concern": details["concern"],
            "branch_time": details["branch_time"],
            "raw_message": prompt.strip()
        }
        send_webhook(payload)
        gsheet_result = append_to_gsheet(st.session_state.gsheet, payload)
        email_result = send_email_alert(payload)
        if gsheet_result and email_result:
            st.toast("Lead saved to Sheet & clinic notified! ✅", icon="✅")
        elif gsheet_result:
            st.toast("Lead saved to Google Sheets! ✅", icon="✅")
        elif email_result:
            st.toast("Clinic notified via email! ✅", icon="✅")
        else:
            st.toast("Patient details saved to local database! ✅", icon="✅")

    response_text = ""
    lower = prompt.lower()

    if "weather" in lower:
        city = "London"
        if "in " in lower:
            parts = lower.split("in ")
            city = parts[-1].strip().title()
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("main"):
                response_text = (
                    f"**Weather in {city}**  \n"
                    f"🌡 Temperature: {res['main']['temp']}°C  \n"
                    f"☁ Conditions: {res['weather'][0]['description'].title()}  \n"
                    f"💧 Humidity: {res['main']['humidity']}%  \n"
                    f"🌬 Wind: {res['wind']['speed']} m/s"
                )
            else:
                response_text = "I couldn't fetch the weather for that location. Please check the city name and try again."
        except Exception:
            response_text = "I'm unable to access the weather service at this moment. Please try again later."

    elif "news" in lower:
        news_key = os.getenv("NEWS_API_KEY", "YOUR_NEWS_API_KEY")
        url = f"https://newsapi.org/v2/top-headlines?country=in&pageSize=5&apiKey={news_key}"
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("articles"):
                lines = ["**Latest Headlines**  \n"]
                for i, a in enumerate(res["articles"][:5], 1):
                    lines.append(f"{i}. **{a['title']}** — {a.get('source', {}).get('name', '')}")
                response_text = "\n\n".join(lines)
            else:
                response_text = "I could not fetch the latest news right now."
        except Exception:
            response_text = "I'm unable to fetch news updates at this time."

    elif "quote" in lower or "motivate" in lower or "inspire" in lower:
        try:
            res = requests.get("https://api.quotable.io/random", timeout=10).json()
            response_text = f"> *\"{res['content']}\"*  \n> \n> — **{res['author']}**"
        except Exception:
            response_text = "Here's a thought: 'The only way to do great work is to love what you do.' — Steve Jobs"

    elif "joke" in lower or "funny" in lower or "humour" in lower or "humor" in lower:
        try:
            res = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode", timeout=10).json()
            if res.get("type") == "single":
                response_text = f"😄 {res['joke']}"
            else:
                response_text = f"😄 {res['setup']}  \n\n{res['delivery']}"
        except Exception:
            response_text = "Why did the AI break up with the internet? Too many connectivity issues! 😄"

    else:
        response_text = ""
        models_to_try = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.0-flash-lite']
        for m_name in models_to_try:
            try:
                resp = client.models.generate_content(model=m_name, contents=f"{SYSTEM_PROMPT}\n\nUser: {prompt}")
                response_text = resp.text
                break
            except Exception as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    continue
                if "429" in str(e):
                    response_text = "I am currently receiving too many requests. Please wait a minute and try asking me again."
                    break
                response_text = f"**Error:** {e}"
                break
        if not response_text:
            response_text = "I'm sorry, I'm unable to process your request right now. Please try again later."

    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
