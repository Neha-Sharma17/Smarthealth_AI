import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import numpy as np
import cv2, os, sys, time, hashlib

sys.path.insert(0, os.getcwd())
from smarthealth_engine import SmartHealthEngine, yt_embed_url, yt_search_url, YT_SONGS

st.set_page_config(page_title="SmartHealth AI", page_icon="🩺",
                   layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
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
</style>
""", unsafe_allow_html=True)

# ── USER DATABASE (saved to users.json so data persists after restart) ────────
USERS_FILE = "users.json"

def load_users():
    import json
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_users(db):
    import json
    with open(USERS_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ── SESSION ───────────────────────────────────────────────────────────────────
for k,v in [("logged_in",False),("user_name",""),("user_email",""),
            ("users_db", load_users()),
            ("engine",None),("scan_count",0),
            ("emotion_counts",{}),("session_start",time.time()),("result",None)]:
    if k not in st.session_state: st.session_state[k]=v

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def do_login(em, pw):
    # Reload from file each time in case another session added a user
    db = load_users()
    st.session_state.users_db = db
    if em not in db: return "Email not found."
    if db[em]["pw"] != hp(pw): return "Wrong password."
    st.session_state.update(logged_in=True, user_name=db[em]["name"], user_email=em)
    return ""

def do_signup(name, em, pw):
    if not name or not em or len(pw) < 6: return "Fill all fields (password min 6 chars)."
    db = load_users()
    if em in db: return "Email already registered."
    db[em] = {"name": name, "pw": hp(pw)}
    save_users(db)
    st.session_state.users_db = db
    st.session_state.update(logged_in=True, user_name=name, user_email=em)
    return ""

def do_logout():
    st.session_state.update(logged_in=False, user_name="", user_email="",
                             scan_count=0, emotion_counts={}, result=None)

COLORS = {"happy":"#2ecc8f","sad":"#4f9eff","angry":"#ff5f6d","neutral":"#7c6fff","sick":"#ffb347"}
EMOJIS = {"happy":"😄","sad":"😢","angry":"😠","neutral":"😐","sick":"🤒"}
EM_ICON = {"happy":"🎵","sad":"💙","angry":"🔥","neutral":"☕","sick":"🧘"}


# ══════════════════════════════════════════════════════════════════════════════
#  MUSIC PLAYER  — THE FIXED VERSION
#  Problem:  st.audio(external_url) fails silently because browsers block
#            cross-origin audio requests from Streamlit's iframe.
#  Fix:      Render an <audio> tag directly inside st.components.v1.html().
#            The browser treats it as a normal page resource — no CORS block.
#  Fallback: If preview_url is empty/None → show YouTube embed instead.
# ══════════════════════════════════════════════════════════════════════════════
def render_music(result):
    em            = result["emotion"]
    deezer_tracks = result.get("deezer_tracks", [])
    yt_songs      = result.get("yt_songs", [])
    color         = COLORS.get(em, "#7c6fff")

    st.markdown(f"""
    <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;
    color:#5a6080;text-transform:uppercase;margin-bottom:12px">
    🎵 Mood music</div>""", unsafe_allow_html=True)

    # Auto-select YouTube tab when Deezer is unreachable
    deezer_ok = bool(deezer_tracks)
    default_tab = 0 if deezer_ok else 1

    tab_deezer, tab_yt = st.tabs(["🟠 Deezer previews", "▶️ YouTube player"])

    # ── TAB 1: DEEZER ─────────────────────────────────────────────────────────
    with tab_deezer:
        if not deezer_ok:
            # Show a soft note + YouTube songs directly inside this tab too
            st.markdown("""
            <div style="background:rgba(255,193,7,.07);border:1px solid rgba(255,193,7,.2);
              border-radius:10px;padding:12px 16px;font-size:13px;color:rgba(255,210,80,.9);
              margin-bottom:14px">
              🌐 Deezer could not be reached on your network right now.<br>
              <strong style="color:#eef0f8">YouTube songs are shown below instead — they play for free.</strong>
            </div>""", unsafe_allow_html=True)
            # Show YouTube songs directly in this tab as fallback
            for title, artist, query in yt_songs:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                  background:#141720;border:1px solid rgba(255,255,255,.06);
                  border-radius:11px;margin-bottom:7px">
                  <div style="width:40px;height:40px;border-radius:8px;
                    background:rgba(255,0,0,.12);display:flex;align-items:center;
                    justify-content:center;font-size:16px;flex-shrink:0">▶</div>
                  <div style="flex:1">
                    <div style="font-size:13px;font-weight:500;color:#eef0f8">{title}</div>
                    <div style="font-size:11px;color:#5a6080">{artist} · YouTube</div>
                  </div>
                  <a href="{yt_search_url(query)}" target="_blank"
                     style="color:#ff4444;font-size:13px;text-decoration:none;
                     background:rgba(255,0,0,.1);border:1px solid rgba(255,0,0,.2);
                     border-radius:8px;padding:5px 10px">Open ↗</a>
                </div>""", unsafe_allow_html=True)
        else:
            has_any_preview = any(t.get("preview_url") for t in deezer_tracks)

            if not has_any_preview:
                st.warning("Deezer returned tracks but **no preview URLs** for this mood query. "
                           "This happens for some regions/tracks. Use the YouTube tab for full songs.")

            for t in deezer_tracks:
                art         = t.get("album_art", "")
                preview_url = t.get("preview_url", "")
                deezer_link = t.get("deezer_url", "#")

                # Song row
                img_html = (f'<img src="{art}" style="width:44px;height:44px;border-radius:9px;object-fit:cover;flex-shrink:0">'
                            if art else
                            f'<div style="width:44px;height:44px;border-radius:9px;background:{color}22;'
                            f'display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0">'
                            f'{EM_ICON.get(em,"🎵")}</div>')

                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:11px;padding:10px 12px;
                  background:#141720;border:1px solid rgba(255,255,255,.06);
                  border-radius:12px;margin-bottom:6px">
                  {img_html}
                  <div style="flex:1;min-width:0">
                    <div style="font-size:13px;font-weight:500;color:#eef0f8;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{t['name']}</div>
                    <div style="font-size:11px;color:#5a6080;margin-top:2px">{t['artist']} · {t['album']}</div>
                  </div>
                  <a href="{deezer_link}" target="_blank"
                     style="color:#ff6600;font-size:22px;text-decoration:none;
                     flex-shrink:0;padding:4px 8px" title="Open on Deezer">▶</a>
                </div>
                """, unsafe_allow_html=True)

                # ── THE ACTUAL FIX: use components.html, NOT st.audio ────────
                if preview_url:
                    components.html(f"""
                    <audio controls preload="none"
                      style="width:100%;height:36px;border-radius:8px;
                             background:#141720;outline:none;margin-top:2px;margin-bottom:10px;
                             filter:invert(1) hue-rotate(180deg)">
                      <source src="{preview_url}" type="audio/mpeg">
                      Your browser does not support audio.
                    </audio>
                    """, height=50)
                else:
                    st.caption("↳ No preview for this track — open on Deezer for full song")

                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;
          background:rgba(255,102,0,.06);border:1px solid rgba(255,102,0,.15);
          border-radius:10px;padding:10px 14px;font-size:12px;color:rgba(255,150,80,.85);margin-top:4px">
          🟠 Deezer is 100% free — no account or API key required.
          30-second previews play directly inside the app.
        </div>""", unsafe_allow_html=True)

    # ── TAB 2: YOUTUBE ────────────────────────────────────────────────────────
    with tab_yt:
        if yt_songs:
            # Embed player for first song
            top_query = yt_songs[0][2]
            components.html(f"""
            <iframe width="100%" height="200"
              src="{yt_embed_url(top_query)}"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
              allowfullscreen
              style="border-radius:12px;display:block">
            </iframe>
            """, height=210)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<div style="font-size:11px;color:#5a6080;margin-bottom:8px">More songs:</div>',
                        unsafe_allow_html=True)

            for title, artist, query in yt_songs:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                      background:#141720;border:1px solid rgba(255,255,255,.06);
                      border-radius:11px;margin-bottom:6px">
                      <div style="width:36px;height:36px;border-radius:8px;
                        background:rgba(255,0,0,.12);display:flex;align-items:center;
                        justify-content:center;font-size:16px;flex-shrink:0">▶</div>
                      <div>
                        <div style="font-size:13px;font-weight:500;color:#eef0f8">{title}</div>
                        <div style="font-size:11px;color:#5a6080">{artist}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f'''<a href="{yt_search_url(query)}" target="_blank"
                        style="display:block;text-align:center;padding:8px;
                        background:#141720;border:1px solid rgba(255,0,0,.3);
                        border-radius:8px;color:#ff4444;text-decoration:none;font-size:13px">
                        Open ↗</a>''', unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:11px;color:#5a6080;margin-top:6px;line-height:1.6">
          ▶ YouTube embed plays full songs for free.
          If it shows "Video unavailable" — click Open ↗ to search directly on YouTube.
        </div>""", unsafe_allow_html=True)


# ── AUTH PAGE ─────────────────────────────────────────────────────────────────
def auth_page():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;margin:48px 0 36px">
          <div style="display:inline-flex;align-items:center;justify-content:center;
            width:68px;height:68px;border-radius:20px;font-size:32px;
            background:linear-gradient(135deg,#7c6fff,#ff6eb4);
            box-shadow:0 0 40px rgba(124,111,255,.35);margin-bottom:16px">🩺</div>
          <div style="font-family:'Syne',sans-serif;font-size:26px;
            color:#eef0f8;letter-spacing:-.5px">SmartHealth AI</div>
          <div style="font-size:13px;color:#5a6080;margin-top:6px">
            Emotion Recognition &amp; Wellness Advisor</div>
        </div>""", unsafe_allow_html=True)

        t1, t2 = st.tabs(["🔑 Sign in", "✨ Create account"])
        with t1:
            em = st.text_input("Email", key="l_em", placeholder="you@example.com")
            pw = st.text_input("Password", type="password", key="l_pw", placeholder="••••••••")
            if st.button("Sign in →", key="login_btn", use_container_width=True):
                err = do_login(em, pw)
                if err: st.error(err)
                else: st.rerun()
            st.caption("No account? Use the Create account tab.")
        with t2:
            nm = st.text_input("Full name", key="s_nm", placeholder="Neha Sharma")
            e2 = st.text_input("Email",     key="s_em", placeholder="you@example.com")
            p2 = st.text_input("Password",  key="s_pw", type="password", placeholder="Min 6 characters")
            if st.button("Create account →", key="su_btn", use_container_width=True):
                err = do_signup(nm, e2, p2)
                if err: st.error(err)
                else: st.rerun()


# ── MAIN APP ──────────────────────────────────────────────────────────────────
def main_app():
    if st.session_state.engine is None:
        with st.spinner("Loading engine..."):
            st.session_state.engine = SmartHealthEngine()
    engine = st.session_state.engine
    fname  = st.session_state.user_name.split()[0]

    st.markdown(f"""
    <div class="app-header">
      <div class="brand">
        <div class="brand-icon">🩺</div>
        <div>
          <div class="brand-name">SmartHealth AI</div>
          <div class="brand-sub">Emotion Recognition &amp; Wellness Advisor — 2026</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:14px">
        <div class="live-pill"><span class="live-dot"></span>Live</div>
        <span style="font-size:13px;color:#5a6080">
          Hi, <strong style="color:#eef0f8">{fname}</strong></span>
      </div>
    </div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.caption(st.session_state.user_email)
        if st.button("🚪 Logout", use_container_width=True):
            do_logout(); st.rerun()
        st.markdown("---")
        st.caption("SmartHealth AI v3.0\nDeezer + YouTube\nNo API key needed!\n\nNeha Sharma, Aditya Sharma & Priyanka Pachauri\nAligarh, UP | 2026")

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")

    # ── LEFT: CAMERA ──────────────────────────────────────────────────────────
    with left:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:1.5px;'
                    'color:#5a6080;text-transform:uppercase;margin-bottom:10px">'
                    'Live camera analysis</div>', unsafe_allow_html=True)
        st.info("💡 Smile with teeth → Happy | Frown → Sad | Normal → Neutral")
        picture = st.camera_input("", label_visibility="collapsed")

        if picture:
            arr   = np.frombuffer(picture.getvalue(), np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is not None:
                with st.spinner("🔍 Analysing emotion..."):
                    result = engine.analyze_frame(frame)
                st.session_state.result = result

                # ── Draw face box + emotion label on the photo ─────────────
                display = frame.copy()
                cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                gray   = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
                faces  = cascade.detectMultiScale(gray, 1.05, 3, minSize=(40,40))
                em_col_bgr = {
                    "happy":   (80, 220, 130),
                    "sad":     (220, 140, 60),
                    "angry":   (80,  80, 240),
                    "neutral": (200, 130, 200),
                    "sick":    (60, 180, 230),
                }.get(result["emotion"], (200,200,200))
                for (fx, fy, fw, fh) in faces:
                    cv2.rectangle(display, (fx, fy), (fx+fw, fy+fh), em_col_bgr, 2)
                    label = f"{result['emotion'].upper()}  {int(result['confidence']*100)}%"
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(display, (fx, fy-th-14), (fx+tw+10, fy), em_col_bgr, -1)
                    cv2.putText(display, label, (fx+5, fy-6),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20,20,30), 2)
                # Convert BGR → RGB for st.image
                display_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                try:
                    st.image(display_rgb, caption="📸 Analysed photo", use_container_width=True)
                except TypeError:
                    st.image(display_rgb, caption="📸 Analysed photo", use_column_width=True)
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                em   = result["emotion"]
                conf = result["confidence"]
                pct  = int(conf * 100)
                col  = COLORS[em]

                st.session_state.scan_count += 1
                cts = st.session_state.emotion_counts
                cts[em] = cts.get(em, 0) + 1

                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;align-items:center;justify-content:space-between">
                    <div>
                      <div style="font-size:10px;color:#5a6080;font-weight:700;
                        letter-spacing:1px;text-transform:uppercase;margin-bottom:5px">
                        Detected emotion</div>
                      <div class="emo-name" style="color:{col}">{em.upper()}</div>
                    </div>
                    <div style="font-size:52px;line-height:1">{EMOJIS[em]}</div>
                  </div>
                  <div style="font-size:12px;color:#8892b0;line-height:1.6;margin-top:10px">
                    {result['suggestion']}</div>
                  <div style="display:flex;justify-content:space-between;
                    font-size:11px;color:#5a6080;margin:12px 0 5px">
                    <span>Confidence</span><span>{pct}%</span></div>
                  <div class="conf-bar">
                    <div class="conf-fill" style="width:{pct}%;background:{col}"></div>
                  </div>
                  <div style="font-size:11px;color:#5a6080;margin-top:8px">
                    Sickness proxy: <strong style="color:#eef0f8">
                    {result['sickness_proxy']:.2f}</strong></div>
                </div>""", unsafe_allow_html=True)

                if em == "happy":   st.success("🎉 Happy vibes!"); st.balloons()
                elif em == "sad":   st.warning("💙 Healing music loading on the right →")
                elif em == "sick":  st.error("🌡️ You look unwell — rest and hydrate!")

        # Stats
        sc  = st.session_state.scan_count
        cts = st.session_state.emotion_counts
        top = max(cts, key=cts.get).capitalize() if cts else "—"
        el  = int(time.time() - st.session_state.session_start)
        ts  = f"{el//60}m {el%60}s" if el >= 60 else f"{el}s"
        st.markdown(f"""
        <div class="stat-grid" style="margin-top:14px">
          <div class="stat-box"><div class="stat-val">{sc}</div>
            <div class="stat-lbl">Scans</div></div>
          <div class="stat-box"><div class="stat-val">{top}</div>
            <div class="stat-lbl">Top mood</div></div>
          <div class="stat-box"><div class="stat-val">{ts}</div>
            <div class="stat-lbl">Session</div></div>
        </div>""", unsafe_allow_html=True)

    # ── RIGHT: INSIGHTS + MUSIC ───────────────────────────────────────────────
    with right:
        result = st.session_state.result
        if result is None:
            st.markdown("""
            <div class="card" style="text-align:center;padding:52px 20px">
              <div style="font-size:52px;opacity:.3;margin-bottom:14px">✨</div>
              <div style="font-size:14px;color:#8892b0">
                Wellness insights &amp; music appear here after a scan</div>
            </div>""", unsafe_allow_html=True)
        else:
            chatbot = result.get("chatbot_data", {})

            # Causes
            causes = chatbot.get("causes", [])
            if causes:
                st.markdown(
                    '<div class="card">'
                    '<div style="font-size:10px;font-weight:700;letter-spacing:1px;'
                    'color:#5a6080;text-transform:uppercase;margin-bottom:12px">'
                    '🔍 Possible causes</div>'
                    + "".join(f'<div class="pill pill-c">{c}</div>' for c in causes)
                    + '</div>', unsafe_allow_html=True)

            # Solutions
            sols = chatbot.get("solutions", [])
            if sols:
                st.markdown(
                    '<div class="card">'
                    '<div style="font-size:10px;font-weight:700;letter-spacing:1px;'
                    'color:#5a6080;text-transform:uppercase;margin-bottom:12px">'
                    '💡 Healing solutions</div>'
                    + "".join(f'<div class="pill pill-s">'
                              f'<strong style="color:#eef0f8">{i+1}.</strong> {s}</div>'
                              for i, s in enumerate(sols))
                    + '</div>', unsafe_allow_html=True)

            # Music (fixed player)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            render_music(result)
            st.markdown('</div>', unsafe_allow_html=True)

    # ── ANALYTICS ─────────────────────────────────────────────────────────────
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,.06);margin:24px 0'>",
                unsafe_allow_html=True)
    st.subheader("📈 Analytics Dashboard")

    @st.cache_data(ttl=10)
    def load_logs():
        if os.path.exists("health_log.csv"):
            try:
                df = pd.read_csv("health_log.csv")
                if not df.empty and len(df.columns) >= 4: return df
            except: pass
        return pd.DataFrame()

    df = load_logs()
    if not df.empty:
        cm = {"happy":"#2ecc8f","sad":"#4f9eff","angry":"#ff5f6d","neutral":"#7c6fff","sick":"#ffb347"}
        kw = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#eef0f8")
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(df.tail(50), names="emotion", title="Emotion distribution",
                         color="emotion", color_discrete_map=cm)
            fig.update_layout(**kw); st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = px.bar(df.tail(20), x="timestamp", y="confidence", color="emotion",
                          title="Recent confidence", color_discrete_map=cm)
            fig2.update_layout(**kw, xaxis_tickangle=-30)
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df.tail(20), use_container_width=True)
        st.download_button("💾 Download CSV", df.to_csv(index=False),
                           "smarthealth_report.csv", "text/csv")
    else:
        st.info("📸 Take your first photo to generate analytics!")

    st.markdown("""
    <div style="text-align:center;color:#5a6080;font-size:12px;padding:24px 0">
      🎓 Final Year B.Tech &nbsp;|&nbsp; OpenCV + Deezer + YouTube + Streamlit &nbsp;|&nbsp;
      Neha Sharma, Aditya Sharma &amp; Priyanka Pachauri &nbsp;|&nbsp; Aligarh, UP &nbsp;|&nbsp; 2026
    </div>""", unsafe_allow_html=True)


# ── ROUTER ────────────────────────────────────────────────────────────────────
if st.session_state.logged_in:
    main_app()
else:
    auth_page()