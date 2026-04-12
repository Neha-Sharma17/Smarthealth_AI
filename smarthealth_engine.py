import cv2
import pandas as pd
import numpy as np
from datetime import datetime
import os, time, requests, urllib.parse

# ── YOUTUBE SONGS ─────────────────────────────────────────────────────────────
YT_SONGS = {
    "happy":   [("Happy",            "Pharrell Williams", "Happy Pharrell Williams official"),
                ("Good as Hell",     "Lizzo",             "Good as Hell Lizzo official"),
                ("Levitating",       "Dua Lipa",          "Levitating Dua Lipa official")],
    "sad":     [("Fix You",          "Coldplay",          "Fix You Coldplay official"),
                ("Skinny Love",      "Bon Iver",          "Skinny Love Bon Iver official"),
                ("Someone Like You", "Adele",             "Someone Like You Adele official")],
    "angry":   [("Lose Yourself",    "Eminem",            "Lose Yourself Eminem official"),
                ("Eye of the Tiger", "Survivor",          "Eye of the Tiger Survivor official"),
                ("Stronger",         "Kanye West",        "Stronger Kanye West official")],
    "neutral": [("Weightless",       "Marconi Union",     "Weightless Marconi Union full"),
                ("Lofi Hip Hop",     "ChilledCow",        "lofi hip hop chill beats study"),
                ("Clair de Lune",    "Debussy",           "Clair de Lune Debussy piano")],
    "sick":    [("Tibetan Bowls",    "Healing Music",     "tibetan singing bowls healing"),
                ("Nature Sounds",    "Relaxing Sleep",    "nature sounds rain healing sleep"),
                ("Moonlight Sonata", "Beethoven",         "Moonlight Sonata Beethoven piano")],
    "fear":    [("Breathe",          "Pink Floyd",        "Breathe Pink Floyd official"),
                ("Clair de Lune",    "Debussy",           "Clair de Lune Debussy piano"),
                ("Weightless",       "Marconi Union",     "Weightless Marconi Union full")],
    "disgust": [("Here Comes the Sun","Beatles",          "Here Comes the Sun Beatles"),
                ("Happy",            "Pharrell Williams", "Happy Pharrell Williams official"),
                ("Good as Hell",     "Lizzo",             "Good as Hell Lizzo official")],
    "surprise":[ ("Uptown Funk",     "Bruno Mars",        "Uptown Funk Bruno Mars official"),
                ("Happy",            "Pharrell Williams", "Happy Pharrell Williams official"),
                ("Can't Stop the Feeling","Justin Timberlake","Can't Stop the Feeling Justin Timberlake")],
}

def yt_search_url(q): return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q)
def yt_embed_url(q):  return "https://www.youtube.com/embed?listType=search&list=" + urllib.parse.quote_plus(q)

# ── DEEZER ────────────────────────────────────────────────────────────────────
class DeezerHelper:
    BASE = "https://api.deezer.com/search"
    MOOD_QUERIES = {
        "happy":   "happy feel good pop upbeat",
        "sad":     "sad healing acoustic comfort",
        "angry":   "calm piano ambient stress relief",
        "neutral": "lofi chill instrumental focus",
        "sick":    "meditation healing relaxing sleep",
        "fear":    "calm meditation ambient peaceful",
        "disgust": "happy uplifting feel good",
        "surprise":"upbeat fun pop dance",
    }
    def mood_tracks(self, emotion, limit=4):
        try:
            r = requests.get(self.BASE,
                params={"q": self.MOOD_QUERIES.get(emotion,"chill"), "limit": limit},
                timeout=5)
            r.raise_for_status()
            out = []
            for t in r.json().get("data", []):
                preview = t.get("preview") or ""
                if len(preview) < 10: preview = ""
                out.append({"name": t["title"], "artist": t["artist"]["name"],
                            "album": t["album"]["title"],
                            "album_art": t["album"].get("cover_medium",""),
                            "preview_url": preview, "deezer_url": t.get("link","")})
            return out
        except:
            return []

# ── ENGINE ────────────────────────────────────────────────────────────────────
class SmartHealthEngine:
    CHATBOT = {
        "happy":   {"causes": ["Achievement or personal success","Strong social connection",
                               "Exercise-released endorphins","Gratitude and mindfulness",
                               "Good sleep and nutrition"],
                    "solutions": ["Share your joy — call a friend","Set a new goal to channel energy",
                                  "Write 3 things you are grateful for","Plan an outdoor activity",
                                  "Meditate 5 min to anchor the feeling"]},
        "sad":     {"causes": ["Loss, grief, or disappointment","Loneliness or isolation",
                               "Stress or burnout","Hormonal changes or poor sleep",
                               "Unresolved past experiences"],
                    "solutions": ["Talk to a trusted friend","Walk 10 minutes in fresh air",
                                  "Write 3 things you are grateful for","Practice 4-7-8 breathing",
                                  "Watch something that makes you smile","Drink warm tea and rest"]},
        "angry":   {"causes": ["Frustration from blocked goals","Feeling of injustice",
                               "Threat to self-esteem","Physical discomfort or pain","Stress overload"],
                    "solutions": ["Breathe: inhale 4s, hold 7s, exhale 8s","Count slowly 10 to 1",
                                  "Walk outside for 5 minutes","Splash cold water on face",
                                  "Write what triggered you","Exercise to burn off adrenaline"]},
        "neutral": {"causes": ["Balanced emotional state","Calm after resolving stress",
                               "Routine low-stimulation day","Mindful transitioning"],
                    "solutions": ["Mindful breathing for 5 minutes","Set a clear intention for next hour",
                                  "Hydrate and have a healthy snack","Do something creative"]},
        "sick":    {"causes": ["Physical illness or fever","Severe fatigue or exhaustion",
                               "Dehydration or malnutrition","Weakened immune system",
                               "Poor sleep for multiple days"],
                    "solutions": ["Drink 2 glasses of water now","Rest — take a 20-minute nap",
                                  "Eat warm soup or broth","Vitamin C: lemon or orange water",
                                  "Steam inhalation with eucalyptus","Avoid screens for 1 hour",
                                  "See a doctor if symptoms persist"]},
        "fear":    {"causes": ["Perceived threat or danger","Anxiety or past trauma",
                               "Uncertainty about the future","Stress or overwhelm"],
                    "solutions": ["Take slow deep breaths (4-7-8)","Ground yourself: name 5 things you see",
                                  "Talk to someone you trust","Remind yourself you are safe",
                                  "Light exercise to release tension"]},
        "disgust": {"causes": ["Exposure to something repulsive","Moral violation","Unpleasant environment",
                               "Bad experience or memory triggered"],
                    "solutions": ["Remove yourself from the situation","Take fresh air outside",
                                  "Drink water and refresh yourself","Do something pleasant",
                                  "Focus on positive things around you"]},
        "surprise":{"causes": ["Unexpected news or event","Pleasant or unpleasant shock",
                               "New information received","Change in routine or plans"],
                    "solutions": ["Take a moment to process","Write down your thoughts",
                                  "Talk to someone about it","Take deep breaths to settle",
                                  "Embrace the change positively"]},
    }
    TIPS = {
        "happy":   "Excellent! Keep it up with exercise and social connection.",
        "sad":     "It is okay. Deep breaths, step outside, call a loved one.",
        "angry":   "Cool down: 4-7-8 breathing — inhale 4s, hold 7s, exhale 8s.",
        "neutral": "Balanced state — a short meditation keeps you sharp.",
        "sick":    "Rest alert: hydrate and rest; see a doctor if needed.",
        "fear":    "You are safe. Breathe slowly and ground yourself.",
        "disgust": "Remove yourself and refresh. Focus on positives.",
        "surprise":"Take a moment to process this unexpected moment.",
    }

    def __init__(self):
        self.log_file = "health_log.csv"
        if not os.path.exists(self.log_file):
            pd.DataFrame(columns=["timestamp","emotion","confidence",
                                   "sickness_proxy","suggestion","method"]
                         ).to_csv(self.log_file, index=False)
        self.last_emotion  = None
        self.last_log_time = 0
        self.deezer        = DeezerHelper()

        # Try to load FER (deep learning — much more accurate)
        self.fer_detector = None
        try:
            import os as _os
            _os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # suppress TF noise
            from fer import FER
            self.fer_detector = FER(mtcnn=False)
            print("✅ FER deep learning detector loaded — high accuracy mode!")
        except ImportError as e:
            print(f"⚠️  FER import error: {e}")
            print("   Run: pip install fer")
            print("   Falling back to HSV method (lower accuracy)")
        except Exception as e:
            print(f"⚠️  FER failed: {e} — using HSV fallback")

        print("✅ SmartHealth Engine ready")

    def analyze_frame(self, frame):
        # ── METHOD 1: FER (deep learning) — use if available ─────────────────
        if self.fer_detector is not None:
            return self._analyze_fer(frame)
        # ── METHOD 2: HSV fallback ───────────────────────────────────────────
        return self._analyze_hsv(frame)

    def _analyze_fer(self, frame):
        """Deep learning emotion detection — works for all skin tones, lighting."""
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.fer_detector.detect_emotions(rgb)

            if not result:
                return self._pack("neutral", 0.4,
                                  "No face detected — move closer or improve lighting.")

            # Get emotion with highest score
            emotions = result[0]["emotions"]
            emotion_raw = max(emotions, key=emotions.get)
            confidence  = round(emotions[emotion_raw], 3)

            print(f"FER | {emotions}")

            # Map FER labels to our labels
            em_map = {
                "happy":   "happy",
                "sad":     "sad",
                "angry":   "angry",
                "neutral": "neutral",
                "fear":    "fear",
                "disgust": "disgust",
                "surprise":"surprise",
            }
            em = em_map.get(emotion_raw, "neutral")

            # Log
            now = time.time()
            if self.last_emotion != em or (now - self.last_log_time) > 10:
                pd.DataFrame([{"timestamp": datetime.now(), "emotion": em,
                               "confidence": confidence, "sickness_proxy": 0,
                               "suggestion": self.TIPS.get(em,"Stay healthy!"),
                               "method": "FER"}]
                             ).to_csv(self.log_file, mode="a", header=False, index=False)
                self.last_emotion  = em
                self.last_log_time = now

            return self._pack(em, confidence, self.TIPS.get(em,"Stay healthy!"))

        except Exception as e:
            print(f"FER error: {e} — switching to HSV")
            return self._analyze_hsv(frame)

    def _analyze_hsv(self, frame):
        """HSV fallback — works without FER installed."""
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.05, 3, minSize=(40,40))

        if len(faces) == 0:
            return self._pack("neutral", 0.3, "No face detected — adjust lighting.")

        faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
        x, y, w, h = faces[0]
        roi = frame[y:y+h, x:x+w]

        mouth    = roi[int(h*0.62):int(h*0.92), int(w*0.15):int(w*0.85)]
        forehead = roi[int(h*0.05):int(h*0.30), int(w*0.20):int(w*0.80)]
        gm = cv2.cvtColor(mouth,    cv2.COLOR_BGR2GRAY).astype(float)
        gf = cv2.cvtColor(forehead, cv2.COLOR_BGR2GRAY).astype(float)

        diff        = float(np.mean(gm)) - float(np.mean(gf))
        mouth_max   = float(np.max(gm))
        mouth_std   = float(np.std(gm))
        smile_score = (diff/30.0) + (mouth_max/255.0) + (mouth_std/60.0)

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        sat = float(np.mean(hsv[:,:,1]))
        val = float(np.mean(hsv[:,:,2]))
        hue = float(np.mean(hsv[:,:,0]))
        sick = round(max(0.0, 1-(sat/100*val/180*0.85)), 2)

        print(f"HSV | smile_score={smile_score:.3f} sat={sat:.1f} val={val:.1f} hue={hue:.1f}")

        if smile_score > 1.25:
            # Happy check is FIRST — smile overrides angry hue
            em, conf = "happy",   min(0.95, 0.60+(smile_score-1.25)*0.15)
        elif sick > 0.75:
            em, conf = "sick",    sick
        elif sat < 35:
            em, conf = "sad",     0.75
        elif hue < 10 and sat > 150 and val > 150:
            # Very strict angry — only genuinely flushed/red face
            em, conf = "angry",   0.70
        else:
            em, conf = "neutral", 0.60

        now = time.time()
        if self.last_emotion != em or (now - self.last_log_time) > 10:
            pd.DataFrame([{"timestamp": datetime.now(), "emotion": em,
                           "confidence": round(conf,3), "sickness_proxy": sick,
                           "suggestion": self.TIPS[em], "method": "HSV"}]
                         ).to_csv(self.log_file, mode="a", header=False, index=False)
            self.last_emotion  = em
            self.last_log_time = now

        return self._pack(em, conf, self.TIPS[em], sick)

    def _pack(self, em, conf, tip, sick=0.0):
        return {
            "emotion":        em,
            "confidence":     conf,
            "suggestion":     tip,
            "sickness_proxy": sick,
            "chatbot_data":   self.CHATBOT.get(em, {}),
            "deezer_tracks":  self.deezer.mood_tracks(em),
            "yt_songs":       YT_SONGS.get(em, []),
        }

if __name__ == "__main__":
    engine = SmartHealthEngine()
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret: break
        r = engine.analyze_frame(frame)
        cv2.putText(frame, r["emotion"].upper(), (10,34),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
        cv2.imshow("SmartHealth", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"): break
    cap.release()
    cv2.destroyAllWindows()