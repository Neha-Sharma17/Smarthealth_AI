# 🩺 SmartHealth AI
### Real-time Emotion Recognition & Wellness Advisor
**Final Year B.Tech Project | 2026**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-red?style=flat-square&logo=streamlit)
![OpenCV](https://img.shields.io/badge/OpenCV-4.10-green?style=flat-square&logo=opencv)
![FER](https://img.shields.io/badge/FER-Deep%20Learning-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📌 Overview

**SmartHealth AI** is a real-time facial emotion recognition system that detects human emotions using deep learning and provides personalized wellness suggestions, healing solutions, and mood-based music recommendations.

Built using **FER (Facial Expression Recognition)** deep learning model with **OpenCV** for face detection, wrapped in a beautiful **Streamlit** dashboard with login/signup system.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 Login / Signup | Secure authentication with SHA-256 password hashing |
| 📸 Real-time Camera | Live photo capture with OpenCV face detection box |
| 🧠 Deep Learning | FER model detects 7 Ekman emotions accurately |
| 💡 Wellness Insights | Causes and healing solutions for each emotion |
| 🎵 Mood Music | YouTube + Deezer songs matched to your emotion |
| 📊 Analytics | Emotion history charts and CSV download |
| 🌙 Dark Theme | Professional dark UI with Space Grotesk font |

---

## 🎭 Emotions Detected

Based on **Paul Ekman's 7 Universal Emotions Theory:**

| Emotion | Emoji | Wellness Action |
|---|---|---|
| Happy | 😄 | Sustain with exercise and social time |
| Sad | 😢 | Breathing exercises, walk, warm tea |
| Angry | 😠 | 4-7-8 breathing technique |
| Neutral | 😐 | Mindful meditation |
| Fear | 😨 | Grounding techniques |
| Disgust | 🤢 | Fresh air, positive focus |
| Surprise | 😲 | Journaling, deep breaths |

---

## 🛠️ Tech Stack

```
Frontend     →  Streamlit 1.38
Face Detection → OpenCV Haar Cascade
Emotion AI   →  FER (Deep Learning CNN) + HSV fallback
Music        →  Deezer API (free) + YouTube embed
Data Storage →  CSV (health logs) + JSON (users)
Security     →  SHA-256 password hashing
```

---

## 📁 Project Structure

```
smarthealth-ai/
│
├── app.py                  # Main Streamlit dashboard
├── smarthealth_engine.py   # Core AI engine (FER + HSV + Deezer)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .gitignore              # Git ignore rules
│
├── health_log.csv          # Auto-generated emotion logs
└── users.json              # Auto-generated user database
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Webcam
- Internet connection (for music)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/smarthealth-ai.git
cd smarthealth-ai
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install streamlit opencv-python pandas pillow plotly requests fer tf-keras
```

**4. Run the app**
```bash
streamlit run app.py
```

**5. Open browser**
```
http://localhost:8501
```

---

## 📸 How It Works

```
1. User logs in / signs up
         ↓
2. Camera captures photo
         ↓
3. OpenCV detects face → draws bounding box
         ↓
4. FER deep learning model analyzes expression
         ↓
5. Emotion classified (happy/sad/angry/neutral/fear/disgust/surprise)
         ↓
6. Wellness causes & solutions displayed
         ↓
7. Mood-matched music recommended (Deezer + YouTube)
         ↓
8. Log saved to health_log.csv for analytics
```

---

## 📊 Accuracy

| Method | Accuracy | Emotions | Speed |
|---|---|---|---|
| FER Deep Learning | ~85-90% | 7 | Fast |
| HSV Fallback | ~55-65% | 5 | Very Fast |
| DeepFace (optional) | ~90%+ | 7 | Moderate |

---

## 🎵 Music Integration

- **Deezer API** — Free, no API key needed, 30-second previews
- **YouTube Embed** — Full songs, free, works when Deezer is unavailable
- Auto-selects songs based on detected emotion

---

## 🔐 Security

- Passwords stored as **SHA-256 hashes** — never plain text
- User data saved locally in `users.json`
- No data sent to any external server

---

## 📈 Future Enhancements

- [ ] Voice emotion detection (NLP)
- [ ] Heart rate estimation from camera
- [ ] Mobile app (React Native)
- [ ] WhatsApp wellness bot
- [ ] Long-term mood trend analysis
- [ ] Spotify API integration (Premium)
- [ ] Multi-language support (Hindi, etc.)

---

## 👩‍💻 Team

| Name | Role |
|---|---|
| **Neha Sharma** | AI & Backend Development |
| **Aditya Sharma** | Frontend & UI Design |
| **Priyanka Pachauri** | Data Analysis & Testing |

**Institution:** Aligarh, Uttar Pradesh | **Year:** 2026

---

## 📄 License

```
MIT License — Free for research and educational use.
For commercial use, contact the authors.
```

---

## 🙏 Acknowledgements

- [FER Library](https://github.com/justinshenk/fer) — Facial Expression Recognition
- [OpenCV](https://opencv.org/) — Computer Vision
- [Streamlit](https://streamlit.io/) — Web Dashboard
- [Deezer API](https://developers.deezer.com/) — Free Music API
- Paul Ekman — 7 Universal Emotions Theory

---

<div align="center">
  Made with ❤️ for healthcare innovation
  <br>
  <strong>SmartHealth AI — Because your emotions matter 🩺</strong>
</div>