import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import cv2, os, sys, time, hashlib, json
from datetime import datetime, date

sys.path.insert(0, os.getcwd())
from smarthealth_engine import SmartHealthEngine, yt_embed_url, yt_search_url, YT_SONGS

st.set_page_config(page_title="SmartHealth AI", page_icon="🩺",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');
*{box-sizing:border-box}
html,body,.stApp{background:#07080d!important;color:#eef0f8!important;font-family:'Space Grotesk',sans-serif!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
.card{background:#1a1d28;border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:18px 20px;margin-bottom:14px}
.app-header{display:flex;align-items:center;justify-content:space-between;padding:14px 28px;background:#0e1018;border-bottom:1px solid rgba(255,255,255,.06)}
.brand{display:flex;align-items:center;gap:12px}
.brand-icon{width:40px;height:40px;border-radius:12px;font-size:20px;background:linear-gradient(135deg,#7c6fff,#ff6eb4);display:flex;align-items:center;justify-content:center;box-shadow:0 0 20px rgba(124,111,255,.3)}
.brand-name{font-family:'Syne',sans-serif;font-size:20px;letter-spacing:-.3px;color:#eef0f8}
.brand-sub{font-size:11px;color:#5a6080}
.live-pill{display:inline-flex;align-items:center;gap:7px;background:rgba(46,204,143,.08);border:1px solid rgba(46,204,143,.2);border-radius:20px;padding:5px 14px;font-size:12px;color:#2ecc8f}
.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#2ecc8f;animation:blink 1.4s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.emo-name{font-family:'Syne',sans-serif;font-size:30px;letter-spacing:-.5px}
.conf-bar{height:5px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden;margin-top:6px}
.conf-fill{height:100%;border-radius:3px;transition:width .8s cubic-bezier(.23,1,.32,1),background .4s}
.pill{font-size:12.5px;color:#8892b0;padding:9px 14px;background:#141720;border-radius:9px;border-left:2.5px solid transparent;line-height:1.55;margin-bottom:7px}
.pill-c{border-left-color:#ff6eb4}.pill-s{border-left-color:#2ecc8f}
.stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.stat-box{background:#1a1d28;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:12px;text-align:center}
.stat-val{font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#eef0f8}
.stat-lbl{font-size:10px;color:#5a6080;margin-top:3px;text-transform:uppercase;letter-spacing:.5px}
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.badge-gold{background:rgba(255,193,7,.15);color:#ffc107;border:1px solid rgba(255,193,7,.3)}
.badge-silver{background:rgba(192,192,192,.15);color:#c0c0c0;border:1px solid rgba(192,192,192,.3)}
.badge-bronze{background:rgba(205,127,50,.15);color:#cd7f32;border:1px solid rgba(205,127,50,.3)}
.badge-green{background:rgba(46,204,143,.15);color:#2ecc8f;border:1px solid rgba(46,204,143,.3)}
.badge-red{background:rgba(255,95,109,.15);color:#ff5f6d;border:1px solid rgba(255,95,109,.3)}
.emergency-card{background:linear-gradient(135deg,rgba(255,95,109,.08),rgba(255,95,109,.03));border:1px solid rgba(255,95,109,.25);border-radius:16px;padding:18px 20px;margin-bottom:12px}
.contact-card{background:#1a1d28;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:center;gap:12px}
.chat-bubble-user{background:linear-gradient(135deg,#7c6fff,#ff6eb4);border-radius:18px 18px 4px 18px;padding:10px 16px;font-size:13px;color:#fff;margin-left:40px;margin-bottom:8px;line-height:1.5}
.chat-bubble-ai{background:#1a1d28;border:1px solid rgba(255,255,255,.07);border-radius:18px 18px 18px 4px;padding:10px 16px;font-size:13px;color:#eef0f8;margin-right:40px;margin-bottom:8px;line-height:1.5}
</style>
""", unsafe_allow_html=True)

# ── FILES ─────────────────────────────────────────────────────────────────────
USERS_FILE    = "users.json"
JOURNAL_FILE  = "journal.json"
GOALS_FILE    = "goals.json"
CONTACTS_FILE = "contacts.json"
CHAT_FILE     = "chat_history.json"

def load_json(f):
    if os.path.exists(f):
        try:
            with open(f) as fp: return json.load(fp)
        except: pass
    return {}

def save_json(f, data):
    with open(f, "w") as fp: json.dump(data, fp, indent=2, default=str)

def load_users():   return load_json(USERS_FILE)
def save_users(db): save_json(USERS_FILE, db)

# ── SESSION ───────────────────────────────────────────────────────────────────
for k,v in [("logged_in",False),("user_name",""),("user_email",""),
            ("users_db",load_users()),("engine",None),("scan_count",0),
            ("emotion_counts",{}),("session_start",time.time()),
            ("result",None),("chat_messages",[])]:
    if k not in st.session_state: st.session_state[k]=v

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def do_login(em,pw):
    db=load_users(); st.session_state.users_db=db
    if em not in db: return "Email not found."
    if db[em]["pw"]!=hp(pw): return "Wrong password."
    st.session_state.update(logged_in=True,user_name=db[em]["name"],user_email=em)
    return ""

def do_signup(name,em,pw):
    if not name or not em or len(pw)<6: return "Fill all fields (password min 6 chars)."
    db=load_users()
    if em in db: return "Email already registered."
    db[em]={"name":name,"pw":hp(pw)}
    save_users(db); st.session_state.users_db=db
    st.session_state.update(logged_in=True,user_name=name,user_email=em)
    return ""

def do_logout():
    st.session_state.update(logged_in=False,user_name="",user_email="",
                             scan_count=0,emotion_counts={},result=None,
                             chat_messages=[])

COLORS={"happy":"#2ecc8f","sad":"#4f9eff","angry":"#ff5f6d","neutral":"#7c6fff",
        "sick":"#ffb347","fear":"#a78bfa","disgust":"#f97316","surprise":"#06b6d4"}
EMOJIS={"happy":"😄","sad":"😢","angry":"😠","neutral":"😐",
        "sick":"🤒","fear":"😨","disgust":"🤢","surprise":"😲"}

# ── WELLNESS SCORE ────────────────────────────────────────────────────────────
def calc_wellness_score():
    if not os.path.exists("health_log.csv"): return 50,"Neutral"
    try:
        df=pd.read_csv("health_log.csv")
        if df.empty: return 50,"Neutral"
        df["timestamp"]=pd.to_datetime(df["timestamp"])
        today=df[df["timestamp"].dt.date==date.today()]
        if today.empty: today=df.tail(20)
        sm={"happy":90,"neutral":65,"surprise":70,"sad":30,"angry":25,"fear":35,"disgust":30,"sick":20}
        scores=[sm.get(e,50) for e in today["emotion"]]
        score=int(np.mean(scores)) if scores else 50
        if score>=75: status="Excellent"
        elif score>=60: status="Good"
        elif score>=45: status="Fair"
        else: status="Needs Care"
        return score,status
    except: return 50,"Neutral"

def score_color(s):
    if s>=75: return "#2ecc8f"
    elif s>=60: return "#7c6fff"
    elif s>=45: return "#ffb347"
    else: return "#ff5f6d"

# ── BADGES ────────────────────────────────────────────────────────────────────
def get_badges(score, scan_count, emotion_counts):
    badges=[]
    if score>=85: badges.append(("🥇","Wellness Champion","badge-gold"))
    elif score>=70: badges.append(("🥈","Wellness Star","badge-silver"))
    elif score>=55: badges.append(("🥉","Getting Better","badge-bronze"))
    if scan_count>=20: badges.append(("📸","Scan Master","badge-green"))
    elif scan_count>=10: badges.append(("📸","Active Scanner","badge-green"))
    if emotion_counts.get("happy",0)>=5: badges.append(("😄","Happy Soul","badge-gold"))
    if scan_count>=1: badges.append(("🌟","First Scan","badge-silver"))
    if not badges: badges.append(("🌱","Just Started","badge-silver"))
    return badges

# ── EXTREME CONDITION CHECK ────────────────────────────────────────────────────
def check_extreme_condition():
    if not os.path.exists("health_log.csv"): return False,""
    try:
        df=pd.read_csv("health_log.csv")
        if len(df)<3: return False,""
        df["timestamp"]=pd.to_datetime(df["timestamp"])
        recent=df.tail(5)
        bad_emotions=["sad","angry","fear","sick"]
        bad_count=sum(1 for e in recent["emotion"] if e in bad_emotions)
        if bad_count>=4:
            top=recent["emotion"].value_counts().index[0]
            msgs={"sad":"Consistent sadness detected. You may need emotional support.",
                  "angry":"High anger levels detected. Please take a break.",
                  "fear":"Anxiety detected repeatedly. Please reach out to someone.",
                  "sick":"You appear unwell consistently. Please rest and see a doctor."}
            return True, msgs.get(top,"You need support right now. Please reach out.")
        return False,""
    except: return False,""

# ── AI CHATBOT RESPONSES ──────────────────────────────────────────────────────
def get_ai_response(user_msg, emotion=None):
    msg = user_msg.lower().strip()
    # Mood-based responses
    if any(w in msg for w in ["sad","unhappy","depressed","cry","crying","upset"]):
        return "💙 I hear you. It's completely okay to feel sad sometimes. You're not alone in this. Try taking 3 deep breaths right now. Would you like to try a breathing exercise or listen to some calming music?"
    if any(w in msg for w in ["happy","great","good","wonderful","amazing","excited"]):
        return "😄 That's wonderful to hear! Your positive energy is infectious! Keep doing what makes you happy. What's making you feel so good today?"
    if any(w in msg for w in ["angry","frustrated","mad","irritated","annoyed"]):
        return "😤 I understand. Anger is a valid emotion. Try this: count to 10 slowly, then take a deep breath. What's causing you to feel this way? Sometimes talking about it helps!"
    if any(w in msg for w in ["anxious","worried","anxiety","stress","stressed","nervous"]):
        return "🌿 Anxiety can feel overwhelming. Let's ground you right now — name 5 things you can see around you. Then take a slow breath in for 4 seconds and out for 6. You are safe. 💚"
    if any(w in msg for w in ["tired","exhausted","fatigue","sleepy","sleep"]):
        return "😴 Your body is asking for rest! Try to sleep by 10:30 PM tonight. Before sleeping, put your phone down and take 3 deep breaths. Rest is medicine — please take it seriously!"
    if any(w in msg for w in ["lonely","alone","isolated","no one","nobody"]):
        return "🤝 Feeling lonely is really hard. But you're not alone — I'm here with you right now! Is there one person you could text or call today? Even a small connection makes a big difference. 💙"
    if any(w in msg for w in ["help","need help","please help","support"]):
        return "🆘 I'm here for you! If you're in a crisis, please call your emergency contact or a helpline immediately. For emotional support, I'm listening — tell me what's going on?"
    if any(w in msg for w in ["motivate","motivation","inspire","give up","giving up"]):
        return "💪 Don't give up! Every single day you wake up is a new chance. Small steps count — even getting out of bed on a hard day is an achievement. What's one tiny thing you can do right now to feel better?"
    if any(w in msg for w in ["thank","thanks","thankful","grateful"]):
        return "🌟 You're very welcome! It makes me happy to be helpful. Remember — you deserve to feel well and happy. Keep going! 💫"
    if any(w in msg for w in ["hi","hello","hey","hlo","hii"]):
        return f"👋 Hello! I'm your SmartHealth AI Wellness Companion. I'm here to listen, support and cheer you up! How are you feeling right now?"
    if any(w in msg for w in ["bye","goodbye","see you","later","exit"]):
        return "👋 Take care of yourself! Remember — your mental health matters. Come back anytime you want to talk. Stay well! 💚"
    if any(w in msg for w in ["meditation","meditate","mindful","mindfulness"]):
        return "🧘 Meditation is amazing! Even 5 minutes daily can reduce stress by 40%. Try this: close your eyes, breathe in for 4 counts, hold for 4, breathe out for 4. Repeat 5 times. How do you feel?"
    if any(w in msg for w in ["music","song","songs","playlist"]):
        return "🎵 Music is great therapy! Go to the Live Scan tab, take a photo, and I'll recommend mood-matched songs for you. Music truly heals the soul! 🎶"
    if any(w in msg for w in ["exercise","workout","gym","walk","running"]):
        return "🏃 Exercise is the best natural antidepressant! Even a 10-minute walk boosts your mood immediately. Can you step outside for a quick walk right now? Your body and mind will thank you! 💪"
    # Emotion context
    if emotion in ["sad","fear"]:
        return "💙 I notice you might be going through a tough time. That's okay — feelings come and go like waves. You are stronger than you think. What's on your mind right now?"
    if emotion == "angry":
        return "Take a moment to breathe. 🌬️ Inhale slowly for 4 seconds... hold for 4... exhale for 6. What's been bothering you? I'm here to listen without judgment."
    if emotion == "happy":
        return "😄 Your happiness is amazing! Tell me what's making your day great? Let's celebrate the good moments together!"
    # Default smart responses
    responses = [
        "🌟 I'm here for you! Tell me more about how you're feeling — talking about it always helps.",
        "💚 That's interesting! Your mental health journey matters. What would make you feel better right now?",
        "🤗 I understand. Everyone has good days and tough days. What's one positive thing that happened today?",
        "💙 Thank you for sharing with me. You're doing great by expressing yourself. What do you need right now?",
        "🌈 Every emotion you feel is valid. Let's work through this together — what's your biggest concern today?",
    ]
    import random
    return random.choice(responses)

# ── MUSIC PLAYER ─────────────────────────────────────────────────────────────
def render_music(result):
    em=result["emotion"]; deezer_tracks=result.get("deezer_tracks",[])
    yt_songs=result.get("yt_songs",[]); color=COLORS.get(em,"#7c6fff")
    st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:1.5px;color:#5a6080;text-transform:uppercase;margin-bottom:12px">🎵 Mood music</div>',unsafe_allow_html=True)
    td,ty=st.tabs(["🟠 Deezer previews","▶️ YouTube player"])
    with td:
        if not deezer_tracks:
            st.markdown('<div style="background:rgba(255,193,7,.07);border:1px solid rgba(255,193,7,.2);border-radius:10px;padding:12px 16px;font-size:13px;color:rgba(255,210,80,.9);margin-bottom:14px">🌐 Deezer not reachable. <strong style="color:#eef0f8">YouTube songs shown below.</strong></div>',unsafe_allow_html=True)
            for title,artist,query in yt_songs:
                st.markdown(f'<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:#141720;border:1px solid rgba(255,255,255,.06);border-radius:11px;margin-bottom:7px"><div style="width:40px;height:40px;border-radius:8px;background:rgba(255,0,0,.12);display:flex;align-items:center;justify-content:center;font-size:16px">▶</div><div style="flex:1"><div style="font-size:13px;font-weight:500;color:#eef0f8">{title}</div><div style="font-size:11px;color:#5a6080">{artist}</div></div><a href="{yt_search_url(query)}" target="_blank" style="color:#ff4444;font-size:13px;text-decoration:none;background:rgba(255,0,0,.1);border:1px solid rgba(255,0,0,.2);border-radius:8px;padding:5px 10px">Open ↗</a></div>',unsafe_allow_html=True)
        else:
            for t in deezer_tracks[:4]:
                art=t.get("album_art",""); purl=t.get("preview_url",""); dl=t.get("deezer_url","#")
                img=f'<img src="{art}" style="width:44px;height:44px;border-radius:9px;object-fit:cover;flex-shrink:0">' if art else f'<div style="width:44px;height:44px;border-radius:9px;background:{color}22;display:flex;align-items:center;justify-content:center;font-size:20px">🎵</div>'
                st.markdown(f'<div style="display:flex;align-items:center;gap:11px;padding:10px 12px;background:#141720;border:1px solid rgba(255,255,255,.06);border-radius:12px;margin-bottom:6px">{img}<div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:500;color:#eef0f8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{t["name"]}</div><div style="font-size:11px;color:#5a6080">{t["artist"]}</div></div><a href="{dl}" target="_blank" style="color:#ff6600;font-size:22px;text-decoration:none;padding:4px 8px">▶</a></div>',unsafe_allow_html=True)
                if purl: components.html(f'<audio controls preload="none" style="width:100%;height:36px;border-radius:8px;filter:invert(1) hue-rotate(180deg);margin-bottom:8px"><source src="{purl}" type="audio/mpeg"></audio>',height=50)
    with ty:
        if yt_songs:
            components.html(f'<iframe width="100%" height="200" src="{yt_embed_url(yt_songs[0][2])}" frameborder="0" allow="autoplay;encrypted-media" allowfullscreen style="border-radius:12px;display:block"></iframe>',height=210)
            st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
            for title,artist,query in yt_songs:
                c1,c2=st.columns([4,1])
                with c1: st.markdown(f'<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:#141720;border:1px solid rgba(255,255,255,.06);border-radius:11px;margin-bottom:6px"><div style="width:36px;height:36px;border-radius:8px;background:rgba(255,0,0,.12);display:flex;align-items:center;justify-content:center;font-size:16px">▶</div><div><div style="font-size:13px;font-weight:500;color:#eef0f8">{title}</div><div style="font-size:11px;color:#5a6080">{artist}</div></div></div>',unsafe_allow_html=True)
                with c2: st.markdown(f'<a href="{yt_search_url(query)}" target="_blank" style="display:block;text-align:center;padding:8px;background:#141720;border:1px solid rgba(255,0,0,.3);border-radius:8px;color:#ff4444;text-decoration:none;font-size:13px">Open ↗</a>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH PAGE
# ══════════════════════════════════════════════════════════════════════════════
def auth_page():
    _,col,_=st.columns([1,1.1,1])
    with col:
        st.markdown('<div style="text-align:center;margin:48px 0 36px"><div style="display:inline-flex;align-items:center;justify-content:center;width:68px;height:68px;border-radius:20px;font-size:32px;background:linear-gradient(135deg,#7c6fff,#ff6eb4);box-shadow:0 0 40px rgba(124,111,255,.35);margin-bottom:16px">🩺</div><div style="font-family:\'Syne\',sans-serif;font-size:26px;color:#eef0f8;letter-spacing:-.5px">SmartHealth AI</div><div style="font-size:13px;color:#5a6080;margin-top:6px">Emotion Recognition &amp; Wellness Advisor</div></div>',unsafe_allow_html=True)
        t1,t2=st.tabs(["🔑 Sign in","✨ Create account"])
        with t1:
            em=st.text_input("Email",key="l_em",placeholder="you@example.com")
            pw=st.text_input("Password",type="password",key="l_pw",placeholder="••••••••")
            if st.button("Sign in →",key="login_btn",use_container_width=True):
                err=do_login(em,pw)
                if err: st.error(err)
                else: st.rerun()
            st.caption("No account? Use the Create account tab.")
        with t2:
            nm=st.text_input("Full name",key="s_nm",placeholder="Your Name")
            e2=st.text_input("Email",key="s_em",placeholder="you@example.com")
            p2=st.text_input("Password",key="s_pw",type="password",placeholder="Min 6 characters")
            if st.button("Create account →",key="su_btn",use_container_width=True):
                err=do_signup(nm,e2,p2)
                if err: st.error(err)
                else: st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def main_app():
    if st.session_state.engine is None:
        with st.spinner("Loading SmartHealth Engine..."):
            st.session_state.engine=SmartHealthEngine()
    engine=st.session_state.engine
    fname=st.session_state.user_name.split()[0]
    score,status=calc_wellness_score()
    sc_col=score_color(score)
    badges=get_badges(score,st.session_state.scan_count,st.session_state.emotion_counts)

    # ── HEADER ────────────────────────────────────────────────────────────────
    badges_html="".join(f'<span class="badge {bc}">{bi} {bn}</span> ' for bi,bn,bc in badges[:3])
    st.markdown(f"""
    <div class="app-header">
      <div class="brand">
        <div class="brand-icon">🩺</div>
        <div><div class="brand-name">SmartHealth AI</div>
        <div class="brand-sub">Emotion Recognition &amp; Wellness Advisor</div></div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        {badges_html}
        <div style="text-align:right">
          <div style="font-size:10px;color:#5a6080;text-transform:uppercase;letter-spacing:.5px">Wellness</div>
          <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:{sc_col}">{score}<span style="font-size:11px;color:#5a6080">/100</span></div>
        </div>
        <div class="live-pill"><span class="live-dot"></span>{status}</div>
        <span style="font-size:13px;color:#5a6080">Hi, <strong style="color:#eef0f8">{fname}</strong></span>
      </div>
    </div>""",unsafe_allow_html=True)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.caption(st.session_state.user_email)
        st.markdown("---")
        st.markdown("**Today's Wellness Score**")
        st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:48px;font-weight:800;color:{sc_col};line-height:1">{score}</div>',unsafe_allow_html=True)
        st.caption(f"Status: **{status}**")
        st.progress(score/100)
        st.markdown("**Your Badges**")
        for bi,bn,bc in badges:
            st.markdown(f'<span class="badge {bc}">{bi} {bn}</span>',unsafe_allow_html=True)
            st.markdown(" ")
        st.markdown("---")
        if st.button("🚪 Logout",use_container_width=True):
            do_logout(); st.rerun()
        st.caption("SmartHealth AI v5.0\nFinal Year B.Tech 2026")

    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)

    # ── ALL TABS ──────────────────────────────────────────────────────────────
    tabs=["📸 Live Scan","🫁 Breathing","📔 Journal","💪 Wellness",
          "🧠 Stress Quiz","🎯 Goals","📊 Analytics",
          "🏆 Achievements","🆘 Emergency","🤖 AI Chat"]
    selected=st.tabs(tabs)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — LIVE SCAN
    # ══════════════════════════════════════════════════════════════════════════
    with selected[0]:
        left,right=st.columns([1,1],gap="large")
        with left:
            st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:1.5px;color:#5a6080;text-transform:uppercase;margin-bottom:10px">Live camera analysis</div>',unsafe_allow_html=True)
            st.info("💡 Smile with teeth → Happy | Frown → Sad | Normal → Neutral")
            picture=st.camera_input("Take photo",label_visibility="collapsed")
            if picture:
                arr=np.frombuffer(picture.getvalue(),np.uint8)
                frame=cv2.imdecode(arr,cv2.IMREAD_COLOR)
                if frame is not None:
                    with st.spinner("🔍 Analysing emotion..."):
                        result=engine.analyze_frame(frame)
                    st.session_state.result=result
                    display=frame.copy()
                    cascade=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
                    faces=cascade.detectMultiScale(cv2.cvtColor(display,cv2.COLOR_BGR2GRAY),1.05,3,minSize=(40,40))
                    em=result["emotion"]; conf=result["confidence"]
                    bgr={"happy":(80,220,130),"sad":(220,140,60),"angry":(80,80,240),
                         "neutral":(200,130,200),"sick":(60,180,230),"fear":(167,139,250),
                         "disgust":(243,115,22),"surprise":(6,182,212)}.get(em,(200,200,200))
                    for (fx,fy,fw,fh) in faces:
                        cv2.rectangle(display,(fx,fy),(fx+fw,fy+fh),bgr,2)
                        label=f"{em.upper()} {int(conf*100)}%"
                        (tw,th),_=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.6,2)
                        cv2.rectangle(display,(fx,fy-th-14),(fx+tw+10,fy),bgr,-1)
                        cv2.putText(display,label,(fx+5,fy-6),cv2.FONT_HERSHEY_SIMPLEX,0.6,(20,20,30),2)
                    try: st.image(cv2.cvtColor(display,cv2.COLOR_BGR2RGB),caption="📸 Analysed photo",use_container_width=True)
                    except TypeError: st.image(cv2.cvtColor(display,cv2.COLOR_BGR2RGB),caption="📸 Analysed photo",use_column_width=True)
                    pct=int(conf*100); col=COLORS.get(em,"#7c6fff")
                    st.session_state.scan_count+=1
                    cts=st.session_state.emotion_counts; cts[em]=cts.get(em,0)+1
                    st.markdown(f"""<div class="card">
                      <div style="display:flex;align-items:center;justify-content:space-between">
                        <div><div style="font-size:10px;color:#5a6080;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:5px">Detected emotion</div>
                        <div class="emo-name" style="color:{col}">{em.upper()}</div></div>
                        <div style="font-size:52px;line-height:1">{EMOJIS.get(em,"😐")}</div>
                      </div>
                      <div style="font-size:12px;color:#8892b0;line-height:1.6;margin-top:10px">{result['suggestion']}</div>
                      <div style="display:flex;justify-content:space-between;font-size:11px;color:#5a6080;margin:12px 0 5px"><span>Confidence</span><span>{pct}%</span></div>
                      <div class="conf-bar"><div class="conf-fill" style="width:{pct}%;background:{col}"></div></div>
                    </div>""",unsafe_allow_html=True)
                    if em=="happy": st.success("🎉 Happy vibes!"); st.balloons()
                    elif em=="sad": st.warning("💙 Healing music loading →")
                    elif em in ["sick","fear"]: st.error("🆘 Go to Emergency tab if needed!")
            sc=st.session_state.scan_count; cts=st.session_state.emotion_counts
            top=max(cts,key=cts.get).capitalize() if cts else "—"
            el=int(time.time()-st.session_state.session_start)
            ts=f"{el//60}m {el%60}s" if el>=60 else f"{el}s"
            st.markdown(f"""<div class="stat-grid" style="margin-top:14px">
              <div class="stat-box"><div class="stat-val">{sc}</div><div class="stat-lbl">Scans</div></div>
              <div class="stat-box"><div class="stat-val">{top}</div><div class="stat-lbl">Top mood</div></div>
              <div class="stat-box"><div class="stat-val">{ts}</div><div class="stat-lbl">Session</div></div>
            </div>""",unsafe_allow_html=True)
        with right:
            result=st.session_state.result
            if result is None:
                st.markdown('<div class="card" style="text-align:center;padding:52px 20px"><div style="font-size:52px;opacity:.3;margin-bottom:14px">✨</div><div style="font-size:14px;color:#8892b0">Take a photo to see wellness insights</div></div>',unsafe_allow_html=True)
            else:
                chatbot=result.get("chatbot_data",{})
                causes=chatbot.get("causes",[])
                if causes:
                    st.markdown('<div class="card"><div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#5a6080;text-transform:uppercase;margin-bottom:12px">🔍 Possible causes</div>'+"".join(f'<div class="pill pill-c">{c}</div>' for c in causes)+'</div>',unsafe_allow_html=True)
                sols=chatbot.get("solutions",[])
                if sols:
                    st.markdown('<div class="card"><div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#5a6080;text-transform:uppercase;margin-bottom:12px">💡 Healing solutions</div>'+"".join(f'<div class="pill pill-s"><strong style="color:#eef0f8">{i+1}.</strong> {s}</div>' for i,s in enumerate(sols))+'</div>',unsafe_allow_html=True)
                st.markdown('<div class="card">',unsafe_allow_html=True)
                render_music(result)
                st.markdown('</div>',unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — BREATHING
    # ══════════════════════════════════════════════════════════════════════════
    with selected[1]:
        st.markdown("## 🫁 Breathing Exercises")
        b1,b2,b3=st.columns(3)
        for col,icon,title,desc,color in [(b1,"😮‍💨","4-7-8 Breathing","Inhale 4s → Hold 7s → Exhale 8s\nBest for: Anxiety & Sleep","#7c6fff"),
                                          (b2,"📦","Box Breathing","4s each phase\nBest for: Focus & Calm","#2ecc8f"),
                                          (b3,"🌬️","Deep Breathing","Inhale 5s → Exhale 5s\nBest for: Relaxation","#4f9eff")]:
            with col:
                st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:32px;margin-bottom:8px">{icon}</div><div style="font-family:\'Syne\',sans-serif;font-size:16px;color:{color};margin-bottom:6px">{title}</div><div style="font-size:12px;color:#5a6080;line-height:1.6">{desc}</div></div>',unsafe_allow_html=True)
        ex=st.selectbox("Choose exercise:",["4-7-8 Breathing","Box Breathing","Deep Breathing"])
        if ex=="4-7-8 Breathing": steps=[("Inhale through nose","4 seconds","#7c6fff"),("Hold your breath","7 seconds","#ffb347"),("Exhale through mouth","8 seconds","#2ecc8f")]
        elif ex=="Box Breathing": steps=[("Inhale","4 seconds","#7c6fff"),("Hold","4 seconds","#ffb347"),("Exhale","4 seconds","#2ecc8f"),("Hold empty","4 seconds","#4f9eff")]
        else: steps=[("Inhale deeply","5 seconds","#7c6fff"),("Exhale slowly","5 seconds","#2ecc8f")]
        components.html(f"""<div style="font-family:'Space Grotesk',sans-serif;padding:20px 0;text-align:center">
          <div id="circle" style="width:160px;height:160px;border-radius:50%;background:rgba(124,111,255,0.1);border:3px solid #7c6fff;margin:0 auto 24px;display:flex;align-items:center;justify-content:center;flex-direction:column;transition:all 1s ease">
            <div id="step-text" style="font-size:15px;font-weight:600;color:#eef0f8;text-align:center;padding:0 10px">Press Start</div>
            <div id="timer-text" style="font-size:36px;font-weight:700;color:#7c6fff;margin-top:4px">0</div>
          </div>
          <button id="startBtn" onclick="startBreathing()" style="padding:12px 32px;border-radius:12px;border:none;background:linear-gradient(135deg,#7c6fff,#ff6eb4);color:white;font-size:14px;font-weight:600;cursor:pointer">▶ Start</button>
          <button id="stopBtn" onclick="stopBreathing()" style="padding:12px 32px;border-radius:12px;border:none;background:#1a1d28;border:1px solid rgba(255,255,255,.1);color:#8892b0;font-size:14px;cursor:pointer;margin-left:10px;display:none">⏹ Stop</button>
        </div>
        <script>
        const steps={json.dumps(steps)};
        let idx=0,cd=0,iv=null,running=false;
        const circ=document.getElementById('circle'),st2=document.getElementById('step-text'),tt=document.getElementById('timer-text');
        function startBreathing(){{running=true;idx=0;document.getElementById('startBtn').style.display='none';document.getElementById('stopBtn').style.display='inline-block';runStep();}}
        function stopBreathing(){{running=false;clearInterval(iv);document.getElementById('startBtn').style.display='inline-block';document.getElementById('stopBtn').style.display='none';st2.textContent='Press Start';tt.textContent='0';circ.style.background='rgba(124,111,255,0.1)';circ.style.borderColor='#7c6fff';circ.style.transform='scale(1)';}}
        function runStep(){{if(!running)return;const[label,dur,color]=steps[idx%steps.length];const d=parseInt(dur);st2.textContent=label;tt.textContent=d;circ.style.background=color+'22';circ.style.borderColor=color;tt.style.color=color;circ.style.transform=label.includes('Inhale')?'scale(1.2)':label.includes('Exhale')?'scale(0.9)':'scale(1.05)';cd=d;iv=setInterval(()=>{{cd--;tt.textContent=cd;if(cd<=0){{clearInterval(iv);idx++;if(running)setTimeout(runStep,300);}}}},1000);}}
        </script>""",height=300)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — JOURNAL
    # ══════════════════════════════════════════════════════════════════════════
    with selected[2]:
        st.markdown("## 📔 Mood Journal")
        jd=load_json(JOURNAL_FILE); uk=st.session_state.user_email.replace("@","_").replace(".","_")
        ue=jd.get(uk,[])
        with st.form("jf"):
            j1,j2=st.columns([3,1])
            with j1: et=st.text_area("How are you feeling?",placeholder="Write your thoughts...",height=100,label_visibility="collapsed")
            with j2:
                mood=st.selectbox("Mood",["😄 Happy","😐 Neutral","😢 Sad","😠 Angry","😨 Anxious","🤩 Excited"],label_visibility="visible")
                energy=st.slider("Energy",1,10,5)
            if st.form_submit_button("💾 Save Entry",use_container_width=True) and et.strip():
                ue.insert(0,{"date":datetime.now().strftime("%d %b %Y, %I:%M %p"),"text":et.strip(),"mood":mood,"energy":energy})
                jd[uk]=ue[:50]; save_json(JOURNAL_FILE,jd); st.success("✅ Saved!"); st.rerun()
        st.markdown("---")
        if not ue: st.info("No entries yet!")
        for entry in ue[:10]:
            mc={"😄":"#2ecc8f","😐":"#7c6fff","😢":"#4f9eff","😠":"#ff5f6d","😨":"#ffb347","🤩":"#ff6eb4"}.get(entry["mood"][0],"#7c6fff")
            st.markdown(f'<div class="card" style="border-left:3px solid {mc}"><div style="display:flex;justify-content:space-between;margin-bottom:8px"><span style="font-size:13px;font-weight:500;color:#eef0f8">{entry["mood"]}</span><span style="font-size:11px;color:#5a6080">{entry["date"]} · Energy: {entry["energy"]}/10</span></div><div style="font-size:13px;color:#8892b0;line-height:1.6">{entry["text"]}</div></div>',unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — WELLNESS
    # ══════════════════════════════════════════════════════════════════════════
    with selected[3]:
        st.markdown("## 💪 Wellness Tips")
        w1,w2=st.columns(2)
        tips=[("😴","Sleep","7-9 hours every night. Sleep before 11 PM.","#7c6fff"),("💧","Hydration","Drink 8 glasses daily. Start with 2 glasses morning.","#4f9eff"),("🏃","Exercise","30 min movement daily — walk, yoga, dance!","#2ecc8f"),("🥗","Nutrition","Eat fruits, vegetables. Reduce sugar and junk.","#ffb347"),("🧘","Mindfulness","5 min meditation daily reduces stress by 40%.","#ff6eb4"),("☀️","Sunlight","20 min morning sun. Boosts Vitamin D and mood.","#f97316"),("📵","Digital Detox","1 hour off screens daily. Read a book instead.","#06b6d4"),("🤝","Social","Connect with one person you care about every day.","#a78bfa")]
        for i,(icon,title,desc,color) in enumerate(tips):
            with (w1 if i%2==0 else w2):
                st.markdown(f'<div class="card"><div style="display:flex;align-items:center;gap:12px;margin-bottom:8px"><div style="width:40px;height:40px;border-radius:10px;background:{color}22;display:flex;align-items:center;justify-content:center;font-size:20px">{icon}</div><div style="font-family:\'Syne\',sans-serif;font-size:15px;color:{color}">{title}</div></div><div style="font-size:12px;color:#8892b0;line-height:1.6">{desc}</div></div>',unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 5 — STRESS QUIZ
    # ══════════════════════════════════════════════════════════════════════════
    with selected[4]:
        st.markdown("## 🧠 Stress Level Quiz")
        questions=[("How often do you feel overwhelmed?",["Rarely","Sometimes","Often","Almost always"]),("How is your sleep quality?",["Very good","Good","Poor","Very poor"]),("How often do you feel anxious?",["Rarely","Sometimes","Often","Almost always"]),("How is your energy level?",["High","Moderate","Low","Very low"]),("How often do you feel irritable?",["Rarely","Sometimes","Often","Almost always"]),("Do you feel in control of your life?",["Yes always","Mostly","Sometimes","Rarely"]),("How often do you take time for yourself?",["Daily","Weekly","Rarely","Never"])]
        answers=[]
        for i,(q,opts) in enumerate(questions):
            answers.append(opts.index(st.radio(f"**{i+1}. {q}**",opts,key=f"sq_{i}",horizontal=True)))
        if st.button("📊 Calculate My Stress Level",use_container_width=True):
            total=sum(answers); mx=len(questions)*3; pct=int(total/mx*100)
            if total<=5: level,color,emoji,msg="Low Stress","#2ecc8f","😊","You are managing stress well! Keep up healthy habits."
            elif total<=10: level,color,emoji,msg="Moderate Stress","#ffb347","😐","Some areas need attention. Try breathing exercises daily."
            elif total<=16: level,color,emoji,msg="High Stress","#ff5f6d","😟","Stress is high. Rest well and talk to someone you trust."
            else: level,color,emoji,msg="Very High Stress","#ff2020","😰","Please seek support. Talk to a counselor. You are not alone."
            st.markdown(f'<div class="card" style="text-align:center;padding:32px;border-left:4px solid {color}"><div style="font-size:52px;margin-bottom:12px">{emoji}</div><div style="font-family:\'Syne\',sans-serif;font-size:28px;color:{color};margin-bottom:8px">{level}</div><div style="font-size:13px;color:#8892b0;line-height:1.6;margin-bottom:16px">{msg}</div><div style="height:8px;background:rgba(255,255,255,.06);border-radius:4px;overflow:hidden"><div style="width:{pct}%;height:100%;background:{color};border-radius:4px"></div></div></div>',unsafe_allow_html=True)
            if total>10:
                st.markdown("### 💡 Recommended Actions")
                for r in ["Practice 4-7-8 breathing twice daily","Write in journal every evening","Get 7-9 hours of sleep","Take a 20-minute walk tomorrow","Talk to a friend or family today"]:
                    st.markdown(f'<div class="pill pill-s">✓ {r}</div>',unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 6 — GOALS
    # ══════════════════════════════════════════════════════════════════════════
    with selected[5]:
        st.markdown("## 🎯 Wellness Goals")
        gd=load_json(GOALS_FILE); uk=st.session_state.user_email.replace("@","_").replace(".","_"); ug=gd.get(uk,[])
        with st.form("gf"):
            g1,g2,g3=st.columns([3,1,1])
            with g1: gt=st.text_input("New goal",placeholder="e.g. Meditate 5 minutes every morning",label_visibility="collapsed")
            with g2: cat=st.selectbox("Category",["😴 Sleep","💧 Water","🏃 Exercise","🧘 Mindfulness","🥗 Nutrition","📵 Screen Time"],label_visibility="collapsed")
            with g3: sg=st.form_submit_button("➕ Add",use_container_width=True)
            if sg and gt.strip():
                ug.append({"text":gt.strip(),"category":cat,"done":False,"created":datetime.now().strftime("%d %b %Y")})
                gd[uk]=ug; save_json(GOALS_FILE,gd); st.rerun()
        if not ug: st.info("No goals yet! Add your first wellness goal above.")
        else:
            done_c=sum(1 for g in ug if g.get("done")); tot_c=len(ug); pct=int(done_c/tot_c*100) if tot_c>0 else 0
            st.markdown(f'<div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><div style="font-size:14px;font-weight:500">Progress: {done_c}/{tot_c} completed</div><div style="font-family:\'Syne\',sans-serif;font-size:20px;color:#2ecc8f">{pct}%</div></div><div style="height:8px;background:rgba(255,255,255,.06);border-radius:4px;overflow:hidden"><div style="width:{pct}%;height:100%;background:#2ecc8f;border-radius:4px"></div></div></div>',unsafe_allow_html=True)
            for i,goal in enumerate(ug):
                c1,c2=st.columns([6,1])
                with c1:
                    chk=st.checkbox(f"{goal['category']}  {goal['text']}",value=goal.get("done",False),key=f"g_{i}")
                    if chk!=goal.get("done",False): ug[i]["done"]=chk; gd[uk]=ug; save_json(GOALS_FILE,gd); st.rerun()
                with c2:
                    if st.button("🗑️",key=f"dg_{i}"): ug.pop(i); gd[uk]=ug; save_json(GOALS_FILE,gd); st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 7 — ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    with selected[6]:
        st.markdown("## 📊 Analytics Dashboard")
        @st.cache_data(ttl=10)
        def load_logs():
            if os.path.exists("health_log.csv"):
                try:
                    df=pd.read_csv("health_log.csv")
                    if not df.empty and len(df.columns)>=4: return df
                except: pass
            return pd.DataFrame()
        df=load_logs()
        if not df.empty:
            df["timestamp"]=pd.to_datetime(df["timestamp"])
            cm={"happy":"#2ecc8f","sad":"#4f9eff","angry":"#ff5f6d","neutral":"#7c6fff","sick":"#ffb347","fear":"#a78bfa","disgust":"#f97316","surprise":"#06b6d4"}
            kw=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#eef0f8")
            total=len(df); top_em=df["emotion"].value_counts().index[0] if total>0 else "—"
            avg_conf=round(df["confidence"].mean()*100) if total>0 else 0
            days=(df["timestamp"].max()-df["timestamp"].min()).days+1 if total>1 else 1
            s1,s2,s3,s4=st.columns(4)
            for col,val,lbl in [(s1,total,"Total Scans"),(s2,top_em.capitalize(),"Top Emotion"),(s3,f"{avg_conf}%","Avg Confidence"),(s4,days,"Days Tracked")]:
                with col: st.markdown(f'<div class="stat-box"><div class="stat-val">{val}</div><div class="stat-lbl">{lbl}</div></div>',unsafe_allow_html=True)
            st.markdown("<div style='height:14px'></div>",unsafe_allow_html=True)
            c1,c2=st.columns(2)
            with c1:
                fig=px.pie(df.tail(50),names="emotion",title="Emotion distribution",color="emotion",color_discrete_map=cm)
                fig.update_layout(**kw); st.plotly_chart(fig,use_container_width=True)
            with c2:
                fig2=px.bar(df.tail(20),x="timestamp",y="confidence",color="emotion",title="Recent confidence",color_discrete_map=cm)
                fig2.update_layout(**kw,xaxis_tickangle=-30); st.plotly_chart(fig2,use_container_width=True)
            df["score_val"]=df["emotion"].map({"happy":90,"neutral":65,"surprise":70,"sad":30,"angry":25,"fear":35,"disgust":30,"sick":20})
            df["date"]=df["timestamp"].dt.date
            daily=df.groupby("date")["score_val"].mean().reset_index()
            fig3=px.line(daily,x="date",y="score_val",title="Wellness score over time",markers=True,color_discrete_sequence=["#7c6fff"])
            fig3.update_layout(**kw); fig3.add_hline(y=60,line_dash="dash",line_color="#2ecc8f",annotation_text="Good threshold")
            st.plotly_chart(fig3,use_container_width=True)
            st.dataframe(df.tail(20),use_container_width=True)
            st.download_button("💾 Download CSV",df.to_csv(index=False),"smarthealth_report.csv","text/csv")
        else: st.info("📸 Take your first photo in Live Scan tab!")

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 8 — ACHIEVEMENTS & BADGES
    # ══════════════════════════════════════════════════════════════════════════
    with selected[7]:
        st.markdown("## 🏆 Achievements & Badges")
        score,_=calc_wellness_score()
        sc=st.session_state.scan_count
        cts=st.session_state.emotion_counts
        all_badges=[
            ("🥇","Wellness Champion","Score 85+","badge-gold",    score>=85),
            ("🥈","Wellness Star",    "Score 70+","badge-silver",  score>=70),
            ("🥉","Getting Better",   "Score 55+","badge-bronze",  score>=55),
            ("📸","Scan Master",      "20+ scans", "badge-green",  sc>=20),
            ("📸","Active Scanner",   "10+ scans", "badge-green",  sc>=10),
            ("📸","First Scan",       "1+ scan",   "badge-silver", sc>=1),
            ("😄","Happy Soul",       "5 happy detections","badge-gold",cts.get("happy",0)>=5),
            ("🧘","Zen Master",       "5 neutral detections","badge-silver",cts.get("neutral",0)>=5),
            ("💪","Resilient",        "Detected anger & recovered","badge-bronze",cts.get("angry",0)>=1),
            ("🌟","Explorer",         "Try all tabs","badge-gold",sc>=5),
            ("📔","Journaler",        "Write 3 journal entries","badge-silver",len(load_json(JOURNAL_FILE).get(st.session_state.user_email.replace("@","_").replace(".","_"),[]))>=3),
            ("🎯","Goal Setter",      "Add 3 goals","badge-bronze",len(load_json(GOALS_FILE).get(st.session_state.user_email.replace("@","_").replace(".","_"),[]))>=3),
        ]
        st.markdown("### 🔓 Earned Badges")
        earned=[b for b in all_badges if b[4]]
        if not earned: st.info("No badges yet — take a scan, write a journal entry, or set a goal!")
        cols=st.columns(4)
        for i,(icon,name,desc,bc,_) in enumerate(earned):
            with cols[i%4]:
                st.markdown(f'<div class="card" style="text-align:center;padding:20px 12px"><div style="font-size:36px;margin-bottom:8px">{icon}</div><div style="font-family:\'Syne\',sans-serif;font-size:14px;color:#eef0f8;margin-bottom:4px">{name}</div><div style="font-size:11px;color:#5a6080">{desc}</div><span class="badge {bc}" style="margin-top:8px;display:inline-flex">Earned ✓</span></div>',unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 🔒 Locked Badges")
        locked=[b for b in all_badges if not b[4]]
        cols2=st.columns(4)
        for i,(icon,name,desc,bc,_) in enumerate(locked):
            with cols2[i%4]:
                st.markdown(f'<div class="card" style="text-align:center;padding:20px 12px;opacity:.4"><div style="font-size:36px;margin-bottom:8px">🔒</div><div style="font-family:\'Syne\',sans-serif;font-size:14px;color:#eef0f8;margin-bottom:4px">{name}</div><div style="font-size:11px;color:#5a6080">{desc}</div></div>',unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 9 — EMERGENCY CONTACTS
    # ══════════════════════════════════════════════════════════════════════════
    with selected[8]:
        st.markdown("## 🆘 Emergency Contacts & Helplines")

        # National helplines
        st.markdown("### 📞 National Mental Health Helplines (India)")
        helplines=[
            ("🧠","iCall — TISS","9152987821","Mon–Sat, 8 AM–10 PM","Free counseling"),
            ("💚","Vandrevala Foundation","1860-2662-345","24/7","Free & Confidential"),
            ("🌸","Snehi","044-24640050","24/7","Emotional support"),
            ("🆘","AASRA","9820466627","24/7","Suicide prevention"),
            ("🏥","National Health Helpline","104","24/7","General health"),
            ("🚑","Ambulance","102","24/7","Medical emergency"),
            ("👮","Police","100","24/7","Emergency"),
            ("🔥","Fire & Emergency","101","24/7","Emergency"),
        ]
        h1,h2=st.columns(2)
        for i,(icon,name,num,timing,desc) in enumerate(helplines):
            with (h1 if i%2==0 else h2):
                st.markdown(f'<div class="emergency-card"><div style="display:flex;align-items:center;gap:12px"><div style="font-size:28px">{icon}</div><div style="flex:1"><div style="font-size:14px;font-weight:600;color:#eef0f8">{name}</div><div style="font-family:\'Syne\',sans-serif;font-size:20px;color:#ff5f6d;font-weight:700">{num}</div><div style="font-size:11px;color:#5a6080">{timing} · {desc}</div></div></div></div>',unsafe_allow_html=True)

        # Family & personal contacts
        st.markdown("---")
        st.markdown("### 👨‍👩‍👧 My Emergency Contacts")
        cd=load_json(CONTACTS_FILE); uk=st.session_state.user_email.replace("@","_").replace(".","_"); uc=cd.get(uk,[])

        with st.form("contact_form"):
            c1,c2,c3,c4=st.columns([2,2,2,1])
            with c1: cn=st.text_input("Name",placeholder="Mom / Best Friend",label_visibility="visible")
            with c2: cp=st.text_input("Phone",placeholder="+91 98765 43210",label_visibility="visible")
            with c3: cr=st.selectbox("Relation",["Family","Friend","Doctor","Therapist","Other"],label_visibility="visible")
            with c4:
                st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
                sc_btn=st.form_submit_button("➕ Add",use_container_width=True)
            if sc_btn and cn.strip() and cp.strip():
                uc.append({"name":cn.strip(),"phone":cp.strip(),"relation":cr,"added":datetime.now().strftime("%d %b %Y")})
                cd[uk]=uc; save_json(CONTACTS_FILE,cd); st.success(f"✅ {cn} added!"); st.rerun()

        if not uc:
            st.info("No personal contacts added yet. Add your family and friends above for quick access during emergencies.")
        else:
            rel_colors={"Family":"#2ecc8f","Friend":"#4f9eff","Doctor":"#ff6eb4","Therapist":"#7c6fff","Other":"#ffb347"}
            for i,c in enumerate(uc):
                rc=rel_colors.get(c["relation"],"#7c6fff")
                col1,col2=st.columns([5,1])
                with col1:
                    st.markdown(f'<div class="contact-card"><div style="width:44px;height:44px;border-radius:50%;background:{rc}22;border:2px solid {rc};display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0">👤</div><div style="flex:1"><div style="font-size:14px;font-weight:600;color:#eef0f8">{c["name"]}</div><div style="font-family:\'Syne\',sans-serif;font-size:18px;color:{rc}">{c["phone"]}</div><div style="font-size:11px;color:#5a6080">{c["relation"]} · Added {c["added"]}</div></div><span class="badge" style="background:{rc}22;color:{rc};border:1px solid {rc}44">{c["relation"]}</span></div>',unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️",key=f"dc_{i}"): uc.pop(i); cd[uk]=uc; save_json(CONTACTS_FILE,cd); st.rerun()

        st.markdown('<div style="background:rgba(255,95,109,.06);border:1px solid rgba(255,95,109,.15);border-radius:12px;padding:16px;margin-top:16px;font-size:13px;color:#8892b0;line-height:1.7">⚠️ <strong style="color:#eef0f8">If you or someone you know is in immediate danger</strong>, please call 112 (Emergency) or 102 (Ambulance) immediately. Your life matters. 💙</div>',unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 10 — AI CHATBOT
    # ══════════════════════════════════════════════════════════════════════════
    with selected[9]:
        st.markdown("## 🤖 AI Wellness Chatbot")
        st.markdown("I'm here to listen, support and boost your mood. Talk to me anytime! 💚")

        em_ctx=st.session_state.result["emotion"] if st.session_state.result else None

        # Show current emotion context
        if em_ctx:
            col=COLORS.get(em_ctx,"#7c6fff"); emoji=EMOJIS.get(em_ctx,"😐")
            st.markdown(f'<div style="display:inline-flex;align-items:center;gap:8px;background:{col}11;border:1px solid {col}33;border-radius:20px;padding:6px 14px;font-size:12px;color:{col};margin-bottom:14px">{emoji} Responding based on your <strong>{em_ctx}</strong> mood</div>',unsafe_allow_html=True)

        # Chat history display
        chat_container=st.container()
        with chat_container:
            if not st.session_state.chat_messages:
                st.markdown('<div class="chat-bubble-ai">👋 Hello! I\'m your SmartHealth AI companion. I\'m here to listen and support you. How are you feeling right now? 💚</div>',unsafe_allow_html=True)
            for msg in st.session_state.chat_messages:
                if msg["role"]=="user":
                    st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>',unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble-ai">{msg["content"]}</div>',unsafe_allow_html=True)

        # Quick mood buttons
        st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
        st.markdown("**Quick messages:**")
        qb=st.columns(4)
        quick_msgs=["I'm feeling sad 😢","I need motivation 💪","I'm stressed 😰","I feel happy 😄"]
        for i,(col,qm) in enumerate(zip(qb,quick_msgs)):
            with col:
                if st.button(qm,key=f"qb_{i}",use_container_width=True):
                    st.session_state.chat_messages.append({"role":"user","content":qm})
                    resp=get_ai_response(qm,em_ctx)
                    st.session_state.chat_messages.append({"role":"assistant","content":resp})
                    st.rerun()

        # Chat input
        with st.form("chat_form",clear_on_submit=True):
            ci1,ci2=st.columns([5,1])
            with ci1: user_input=st.text_input("Type your message...",label_visibility="collapsed",placeholder="How are you feeling? Tell me anything...")
            with ci2: send=st.form_submit_button("Send 💬",use_container_width=True)
            if send and user_input.strip():
                st.session_state.chat_messages.append({"role":"user","content":user_input})
                resp=get_ai_response(user_input,em_ctx)
                st.session_state.chat_messages.append({"role":"assistant","content":resp})
                st.rerun()

        # Clear chat button
        if st.session_state.chat_messages:
            if st.button("🗑️ Clear chat",use_container_width=False):
                st.session_state.chat_messages=[]; st.rerun()

        st.markdown('<div style="font-size:11px;color:#5a6080;margin-top:12px;text-align:center">💙 This AI provides emotional support only. For medical emergencies, please contact a professional or use the Emergency tab.</div>',unsafe_allow_html=True)

    # Footer
    st.markdown('<div style="text-align:center;color:#5a6080;font-size:12px;padding:24px 0;border-top:1px solid rgba(255,255,255,.06);margin-top:20px">🎓 Final Year B.Tech &nbsp;|&nbsp; OpenCV + FER + Streamlit &nbsp;|&nbsp; 2026</div>',unsafe_allow_html=True)

# ── ROUTER ────────────────────────────────────────────────────────────────────
if st.session_state.logged_in:
    main_app()
else:
    auth_page()