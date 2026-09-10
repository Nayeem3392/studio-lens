import streamlit as st
import cv2
import numpy as np
import librosa
import os
import tempfile
import subprocess
import pandas as pd
import time
import base64
import imageio_ffmpeg

# ---------- PAGE CONFIG (MUST BE FIRST) ----------
st.set_page_config(
    page_title="Studio Lens",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- PERMANENT IMAGE LOADING ----------
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, "drone.png")

if os.path.exists(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    drone_src = f"data:image/png;base64,{encoded_string}"
else:
    # Fallback: The cute ghost image you uploaded
    drone_src = "https://cdn-icons-png.flaticon.com/512/3588/3588920.png"

# ---------- INJECT CINEMATIC DARK MODE UI ----------
st.markdown("""
<style>
    /* ---- FORCE CINEMATIC DARK THEME ---- */
    .stApp, body {
        background-color: #0B1120 !important; /* Deep Slate Blue */
        color: #F8FAFC !important; /* Pure White Text */
    }
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stMetricValue {
        color: #F8FAFC !important;
    }
    
    /* ---- FIX THE FILE UPLOADER ---- */
    [data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 2px dashed #334155 !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #06B6D4 !important; 
        background-color: #0F172A !important;
    }
    [data-testid="stFileUploader"] label {
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }
    .uploadedFile {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border-radius: 8px !important;
    }
    
    /* Fix Text Inputs */
    .stTextInput input {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
    }
    .stTextInput input:focus {
        border-color: #06B6D4 !important;
        box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2) !important;
    }
    
    /* ---- Hide Default Streamlit Elements ---- */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ---- Fixed Navigation Bar ---- */
    .navbar {
        position: fixed;
        top: 0; left: 0;
        width: 100%;
        background: rgba(11, 17, 32, 0.85) !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid #1E293B;
        padding: 0.8rem 3rem;
        z-index: 999;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-sizing: border-box;
    }
    .nav-logo {
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: -0.03em;
        color: #F8FAFC !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nav-logo span { color: #06B6D4 !important; }
    .nav-links {
        display: flex;
        gap: 2rem;
        align-items: center;
    }
    .nav-links a {
        text-decoration: none;
        color: #94A3B8 !important;
        font-size: 0.9rem;
        font-weight: 500;
        transition: color 0.2s;
    }
    .nav-links a:hover { color: #F8FAFC !important; }
    .nav-cta {
        background: #1E293B;
        color: #06B6D4 !important;
        padding: 0.4rem 1.2rem;
        border-radius: 40px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #334155;
    }

    /* ---- Hero Section ---- */
    .hero {
        margin-bottom: 2rem;
        position: relative;
        z-index: 10;
        padding-top: 80px;
    }
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #F8FAFC !important;
        margin-bottom: 0.5rem;
        line-height: 1.1;
    }
    .hero h1 span {
        background: linear-gradient(135deg, #8B5CF6, #06B6D4); /* Purple to Cyan */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero p {
        font-size: 1.1rem;
        color: #94A3B8 !important;
        max-width: 600px;
        font-weight: 400;
        margin-top: 0;
    }

    /* ---- Glassmorphism Cards ---- */
    .glass-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(6, 182, 212, 0.1);
        border-color: #06B6D4;
    }

    /* ---- Modern Buttons ---- */
    .stButton button {
        background: linear-gradient(135deg, #8B5CF6, #06B6D4) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #7C3AED, #0891B2) !important;
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
    }

    /* ---- Metrics ---- */
    .stMetric {
        background: #1E293B;
        padding: 1.2rem !important;
        border-radius: 12px !important;
        border: 1px solid #334155;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em;
    }
    .stMetric .stMetricValue {
        color: #F8FAFC !important;
        font-weight: 800 !important;
        font-size: 1.5rem !important;
    }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #1E293B;
        border-radius: 12px;
        padding: 0.3rem;
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94A3B8 !important;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background: #0B1120 !important;
        color: #06B6D4 !important;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
    }

    /* ---- Expanders ---- */
    .streamlit-expanderHeader {
        background: #1E293B !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        color: #F8FAFC !important;
        font-weight: 600 !important;
        padding: 1rem !important;
    }
    .streamlit-expanderHeader:hover {
        background: #0F172A !important;
        border-color: #06B6D4 !important;
    }
    .streamlit-expanderContent {
        background: #0F172A !important;
        border: 1px solid #334155 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1.5rem !important;
    }

    /* ---- Chat Input ---- */
    .stChatInput input {
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 0.8rem 1.5rem !important;
        background: #1E293B !important;
        color: #F8FAFC !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .stChatInput input:focus {
        border-color: #06B6D4 !important;
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.2) !important;
    }

    /* ---- Footer ---- */
    .footer {
        margin-top: 4rem;
        padding-top: 2rem;
        border-top: 1px solid #1E293B;
        color: #64748B !important;
        font-size: 0.8rem;
        text-align: center;
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
    }
    .footer span { color: #06B6D4 !important; font-weight: bold; }

    /* ---- Drone Mascot (Floating & Blended) ---- */
    .drone-mascot {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 120px;
        z-index: 10000;
        pointer-events: none;
        animation: floatDrone 4s ease-in-out infinite alternate;
        mix-blend-mode: screen; 
        filter: drop-shadow(0 10px 10px rgba(0,0,0,0.5));
    }
    @keyframes floatDrone {
        0% { transform: translateY(0px) rotate(-3deg); }
        100% { transform: translateY(-15px) rotate(3deg); }
    }
    .drone-img {
        width: 100%;
        height: auto;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# ---------- NAVBAR ----------
st.markdown("""
<div class="navbar">
    <div class="nav-logo">◆ <span>Studio Lens</span></div>
    <div class="nav-links">
        <a href="#">Dashboard</a>
        <a href="#">Guides</a>
        <a href="#">API</a>
        <a href="#" class="nav-cta">Beta</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ---- HERO SECTION ----
st.markdown("""
<div class="hero">
    <h1>Video Intelligence <span>Studio Lens</span></h1>
    <p>Upload a video or paste a link to automatically decode its editing DNA — color grading, transitions, audio structure, and motion patterns.</p>
</div>
""", unsafe_allow_html=True)

# ---- BACKEND FUNCTIONS ----
def extract_audio(video_path):
    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, "temp_audio.wav")
    try:
        # Bulletproof fix: use the bundled ffmpeg from imageio-ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [ffmpeg_exe, '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', audio_path, '-y'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"Audio extraction failed: {str(e)}")
        return None
    return audio_path

def analyze_audio(audio_path):
    if not audio_path or not os.path.exists(audio_path):
        return None, None, None
    try:
        y, sr = librosa.load(audio_path, duration=30)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo[0]) if hasattr(tempo, '__len__') else float(tempo)
        energy = float(np.sum(librosa.feature.rms(y=y)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=y)))
        is_speech = zcr > 0.05
        return tempo, energy, is_speech
    except Exception:
        return None, None, None

def detect_color_style(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    sat = np.mean(hsv[:, :, 1])
    val = np.mean(hsv[:, :, 2])
    if sat < 30: return "Black & White"
    b, g, r = cv2.split(frame)
    avg_r, avg_g, avg_b = np.mean(r), np.mean(g), np.mean(b)
    if avg_r > avg_g > avg_b and avg_r - avg_b > 20: return "Sepia / Vintage"
    dark_mask = val < 100
    bright_mask = val > 150
    if np.any(dark_mask) and np.any(bright_mask):
        dark_hue = np.mean(hsv[:, :, 0][dark_mask])
        bright_hue = np.mean(hsv[:, :, 0][bright_mask])
        if (10 <= bright_hue <= 25) and (100 <= dark_hue <= 130): return "Teal & Orange"
    if avg_r > avg_b: return "Warm"
    elif avg_b > avg_r: return "Cool"
    return "Normal"

def detect_brightness_contrast(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray), np.std(gray)

def detect_transitions(frames, threshold_cut=30.0):
    transitions = []
    for i in range(1, len(frames)):
        prev, curr = frames[i-1], frames[i]
        diff = cv2.absdiff(prev, curr)
        if np.mean(diff) > threshold_cut:
            transitions.append((i, "Cut"))
        else:
            prev_b, curr_b = np.mean(prev), np.mean(curr)
            if prev_b > 100 and curr_b < 20: transitions.append((i, "Fade to Black"))
            elif prev_b < 20 and curr_b > 100: transitions.append((i, "Fade from Black"))
            else:
                prev_corners = cv2.goodFeaturesToTrack(prev, maxCorners=50, qualityLevel=0.01, minDistance=10)
                if prev_corners is not None:
                    curr_corners, status, _ = cv2.calcOpticalFlowPyrLK(prev, curr, prev_corners, None)
                    if curr_corners is not None and status is not None:
                        good_new, good_old = curr_corners[status == 1], prev_corners[status == 1]
                        if len(good_new) > 5:
                            motion = good_new - good_old
                            h, w = prev.shape
                            center = np.array([w/2, h/2])
                            avg_old = np.mean(np.linalg.norm(good_old - center, axis=1))
                            avg_new = np.mean(np.linalg.norm(good_new - center, axis=1))
                            if avg_new > avg_old * 1.2: transitions.append((i, "Zoom In"))
                            elif avg_new < avg_old * 0.8: transitions.append((i, "Zoom Out"))
                            else:
                                dx, dy = np.mean(motion[:, 0]), np.mean(motion[:, 1])
                                if abs(dx) > 2 and abs(dy) < 1: transitions.append((i, "Slide / Pan"))
    return transitions

def detect_camera_motion(frames):
    if len(frames) < 2: return "Static"
    prev, curr = frames[0], frames[-1]
    prev_corners = cv2.goodFeaturesToTrack(prev, maxCorners=100, qualityLevel=0.01, minDistance=10)
    if prev_corners is None: return "Static"
    curr_corners, status, _ = cv2.calcOpticalFlowPyrLK(prev, curr, prev_corners, None)
    if curr_corners is None or status is None: return "Static"
    good_new, good_old = curr_corners[status == 1], prev_corners[status == 1]
    if len(good_new) < 5: return "Static"
    motion = good_new - good_old
    dx, dy = np.mean(motion[:, 0]), np.mean(motion[:, 1])
    if abs(dx) > 10 and abs(dy) < 5: return "Panning horizontally"
    elif abs(dy) > 10 and abs(dx) < 5: return "Tilting vertically"
    elif abs(dx) < 3 and abs(dy) < 3: return "Static"
    else: return "Camera moving (pan/tilt)"

def detect_text_presence(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    h, w = edges.shape
    top = edges[:int(h*0.3), :]
    bottom = edges[int(h*0.7):, :]
    top_density = np.sum(top > 0) / (top.shape[0] * top.shape[1])
    bottom_density = np.sum(bottom > 0) / (bottom.shape[0] * bottom.shape[1])
    return (top_density > 0.05 or bottom_density > 0.05)

def analyze_video(video_path, progress_callback=None):
    results = {}
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    results['duration'] = frame_count / fps if fps > 0 else 0
    results['fps'] = fps

    sample_rate = 2
    sample_interval = max(1, int(fps / sample_rate))
    frames, color_frames = [], []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        if frame_idx % sample_interval == 0:
            small = cv2.resize(frame, (320, 180))
            frames.append(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
            color_frames.append(small)
        frame_idx += 1
    cap.release()

    if progress_callback: progress_callback(0.3, "Detecting transitions...")
    results['transitions'] = detect_transitions(frames)

    if progress_callback: progress_callback(0.5, "Analyzing camera motion...")
    results['camera_motion'] = detect_camera_motion(frames)

    if progress_callback: progress_callback(0.6, "Analyzing colors...")
    color_votes = {}
    for cframe in color_frames:
        style = detect_color_style(cframe)
        color_votes[style] = color_votes.get(style, 0) + 1
    results['dominant_color'] = max(color_votes, key=color_votes.get) if color_votes else "Unknown"

    brightness_list, contrast_list = [], []
    for cframe in color_frames:
        b, c = detect_brightness_contrast(cframe)
        brightness_list.append(b)
        contrast_list.append(c)
    results['avg_brightness'] = np.mean(brightness_list)
    results['avg_contrast'] = np.mean(contrast_list)

    if progress_callback: progress_callback(0.75, "Detecting text...")
    sample_frames_for_text = color_frames[::max(1, len(color_frames)//5)]
    text_present_frames = sum(1 for frame in sample_frames_for_text if detect_text_presence(frame))
    results['text_overlay'] = text_present_frames > (len(sample_frames_for_text) // 2)
    results['objects'] = []

    annotated_frames = []
    for i, frame in enumerate(color_frames[:5]):
        style = detect_color_style(frame)
        annotated = frame.copy()
        cv2.putText(annotated, style, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        annotated_frames.append(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
    results['annotated_frames'] = annotated_frames

    if progress_callback: progress_callback(0.9, "Extracting audio...")
    audio_path = extract_audio(video_path)
    tempo, energy, is_speech = analyze_audio(audio_path)
    results['tempo'] = tempo
    results['energy'] = energy
    results['is_speech'] = is_speech
    if audio_path and os.path.exists(audio_path): os.remove(audio_path)

    if progress_callback: progress_callback(1.0, "Done!")
    return results

def get_recommendations(results):
    recs = []
    color = results['dominant_color']
    if color == "Teal & Orange":
        recs.append({"feature": "Teal & Orange Color Grade", "steps": ["Open **CapCut** (free) – [Download](https://www.capcut.com/)", "Import your video: tap 'New project' → select video.", "Tap the clip → **Filters** → search 'Teal Orange'.", "Apply filter, adjust strength.", "Alternatively in **DaVinci Resolve** – [Download](https://www.blackmagicdesign.com/products/davinciresolve)", "Go to **Color** page → use **Color Wheels**: shadows to blue, highlights to orange.", "Free LUTs: [freeluts.com](https://www.freeluts.com/)"], "assets": "No extra assets needed.", "ai_prompt": "AI prompt: 'Cinematic teal and orange color graded scene, high contrast, film look'"})
    elif color == "Sepia / Vintage":
        recs.append({"feature": "Sepia / Vintage Look", "steps": ["Open **CapCut** – [Download](https://www.capcut.com/)", "Import video, tap clip → **Filters** → search 'Sepia' or 'Vintage'.", "Apply filter.", "For film grain: search 'free film grain overlay' on YouTube, download, place over clip, blend mode **Overlay** or **Screen**, low opacity."], "assets": "Film grain: [YouTube search](https://www.youtube.com/results?search_query=free+film+grain+overlay)", "ai_prompt": "AI prompt: 'Old vintage sepia film look, scratches, warm tones'"})
    elif color == "Black & White":
        recs.append({"feature": "Black & White", "steps": ["Set Saturation to 0: CapCut → clip → **Adjust** → **Saturation** → 0.", "Or apply 'Black & White' filter from **Filters**."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'High contrast black and white cinematic shot'"})
    elif color == "Warm":
        recs.append({"feature": "Warm Color Tone", "steps": ["In CapCut: clip → **Adjust** → **Temperature** → move slider right (+20)."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'Warm sunset lighting, golden hour, cozy atmosphere'"})
    elif color == "Cool":
        recs.append({"feature": "Cool Color Tone", "steps": ["In CapCut: clip → **Adjust** → **Temperature** → move slider left (-20)."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'Cool blue moonlight, icy tones, calm mood'"})

    if results['avg_contrast'] > 70: recs.append({"feature": "High Contrast", "steps": ["Increase contrast: clip → **Adjust** → **Contrast** → +30."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'High contrast dramatic lighting, deep shadows, bright highlights'"})
    elif results['avg_contrast'] < 40: recs.append({"feature": "Low Contrast (Soft Look)", "steps": ["Decrease contrast: clip → **Adjust** → **Contrast** → -30."], "assets": "Optional: add slight blur or diffusion.", "ai_prompt": "AI prompt: 'Soft low contrast dreamy look, pastel colors'"})

    if results['transitions']:
        transition_counts = {}
        for _, ttype in results['transitions']: transition_counts[ttype] = transition_counts.get(ttype, 0) + 1
        for ttype, count in transition_counts.items():
            if ttype == "Cut": recs.append({"feature": "Cuts", "steps": ["Place clips next to each other with no transition."], "assets": "No assets needed.", "ai_prompt": "Not applicable"})
            elif "Fade" in ttype: recs.append({"feature": "Fade Transitions", "steps": ["In CapCut: tap transition box → choose 'Fade' or 'Dissolve'. Adjust duration."], "assets": "Built-in transitions.", "ai_prompt": "Not applicable"})
            elif "Zoom" in ttype: recs.append({"feature": "Zoom Transitions", "steps": ["In CapCut: transition box → search 'Zoom' → apply. Or keyframe scale in Premiere."], "assets": "Built-in transitions.", "ai_prompt": "Not applicable"})
            elif "Slide" in ttype: recs.append({"feature": "Slide / Pan Transitions", "steps": ["In CapCut: transition box → search 'Slide'. Or keyframe position manually."], "assets": "Built-in transitions.", "ai_prompt": "Not applicable"})

    if results['camera_motion'] != "Static": recs.append({"feature": f"Camera Movement: {results['camera_motion']}", "steps": ["To recreate: use gimbal or steady hand when filming.", "Or add digital movement: keyframe Position/Scale in editor."], "assets": "No assets needed.", "ai_prompt": "Not applicable"})
    if results['text_overlay']: recs.append({"feature": "Text Overlay Detected", "steps": ["Add text: CapCut → **Text** → **Add Text**.", "Type text, adjust font, size, color.", "Premiere Pro: use Type Tool (T)."], "assets": "Free fonts: [Google Fonts](https://fonts.google.com/)", "ai_prompt": "Not applicable"})

    if results['tempo']:
        if results['tempo'] > 120: mood = "fast / energetic"
        elif results['tempo'] > 90: mood = "moderate"
        else: mood = "slow / calm"
        recs.append({"feature": f"Music ({mood}, {results['tempo']:.0f} BPM)", "steps": [f"Go to free music site: [YouTube Audio Library](https://www.youtube.com/audiolibrary), [Pixabay Music](https://pixabay.com/music/).", f"Search for '{mood} music {results['tempo']:.0f} BPM'.", "Download and import into editor.", "Align with video length."], "assets": f"Search term: 'royalty free {mood} music {results['tempo']:.0f} BPM'", "ai_prompt": f"AI prompt: 'Upbeat electronic track at {results['tempo']:.0f} BPM, energetic'"})
    if results['is_speech']: recs.append({"feature": "Voiceover / Dialogue", "steps": ["Record with microphone, or use AI voice: [ElevenLabs](https://elevenlabs.io/), [Play.ht](https://play.ht/).", "Import and place on audio track."], "assets": "AI voices: ElevenLabs, Play.ht", "ai_prompt": "AI prompt: 'Professional voice, confident, explaining product, 30 seconds'"})

    return recs

def answer_question(question, results=None):
    q = question.lower().strip()
    yt_search = f"https://www.youtube.com/results?search_query={question.replace(' ', '+')}"
    google_search = f"https://www.google.com/search?q={question.replace(' ', '+')}"

    if any(word in q for word in ["star", "sparkle", "glitter", "particle", "magic dust", "stars"]):
        return "**✨ How to add Star / Sparkle / Particle Effects:**\n\n1. Open **CapCut** (free) – [Download](https://www.capcut.com/)\n2. Tap on your clip, then tap **Overlays** or **Effects**.\n3. Search for 'stars', 'sparkles', 'particles', or 'magic'.\n4. Choose an overlay (e.g., 'Sparkle' or 'Star').\n5. Drag it on top of your video and adjust size/position.\n6. Change blend mode to **Screen** or **Add** to remove black background.\n\n**Alternative in Premiere Pro:**\n1. Go to **Effects** panel, search 'Particle' or 'Star'.\n2. Drag onto your clip.\n3. Or use free overlay videos from [Pexels](https://www.pexels.com/search/videos/stars/) or [Pixabay](https://pixabay.com/videos/search/stars/).\n\n" + f"🎥 **Video Tutorial:** [Watch on YouTube]({yt_search})\n🔎 **More resources:** [Google]({google_search})"
    if any(word in q for word in ["overlay", "light leak", "film burn", "bokeh", "dust"]):
        return "**🎞️ How to add Overlay Effects (light leaks, bokeh, dust):**\n\n1. Download free overlays from [Pexels](https://www.pexels.com/search/videos/overlay/) or [Pixabay](https://pixabay.com/videos/search/overlay/).\n2. Import the overlay into your editor.\n3. Place it on a track **above** your main video.\n4. Change blend mode to **Screen** (or **Overlay** for subtle effect).\n5. Adjust opacity and size as needed.\n\n" + f"🎥 **Video Tutorial:** [Watch on YouTube]({yt_search})\n🔎 **More resources:** [Google]({google_search})"
    if any(word in q for word in ["intro", "outro", "start effect", "opening"]):
        return "**🎬 How to add Intro / Start Effects:**\n\n1. In **CapCut**: Tap 'Effects' → search 'Intro' or 'Opening'.\n2. Choose a template or effect and drag it to the beginning.\n3. Use **Text Animation**: tap 'Text' → 'Add Text', type title, then 'Animation' → choose entrance animation.\n4. For advanced intros, use **Canva** (free) – [canva.com](https://www.canva.com/) and search 'video intro templates'.\n5. Export and import into your editor.\n\n" + f"🎥 **Video Tutorial:** [Watch on YouTube]({yt_search})\n🔎 **More resources:** [Google]({google_search})"
    if any(word in q for word in ["fade", "dissolve"]): return "**🌑 Fade Transition:**\nIn CapCut: tap the small square between clips → choose 'Fade' or 'Dissolve'. Adjust duration.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if "cut" in q and "transition" in q: return "**✂️ Cut Transition:**\nJust place two clips next to each other with no gap. No transition needed.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["zoom transition", "zoom in", "zoom out"]): return "**🔍 Zoom Transition:**\nCapCut: transition box → search 'Zoom' → apply. Or keyframe scale in Premiere Pro.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["slide", "pan transition", "whip"]): return "**↔️ Slide / Whip Transition:**\nCapCut: transition box → search 'Slide' or 'Whip'. Or keyframe position.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["glitch", "rgb", "digital"]): return "**📺 Glitch Transition:**\nCapCut: search 'Glitch' in transitions. Or use free glitch overlay videos from Pixabay.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["teal", "orange", "color grade", "cinematic color", "lut"]): return "**🎨 Teal & Orange Color Grade:**\nCapCut: Filters → search 'Teal Orange'. Or DaVinci Resolve Color Wheels. Free LUTs: freeluts.com.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["sepia", "vintage", "retro", "old film"]): return "**📜 Sepia/Vintage:**\nCapCut: Filters → search 'Sepia'. Add film grain overlay.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["black and white", "b&w", "monochrome"]): return "**⬛ Black & White:**\nSet Saturation to 0, or apply B&W filter.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if "contrast" in q: return "**🌗 Contrast:**\nCapCut: Adjust → Contrast. Increase for high contrast, decrease for soft.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if "music" in q or "audio" in q or "bpm" in q:
        if results and results.get('tempo'):
            tempo = results['tempo']
            mood = "fast" if tempo > 120 else "moderate" if tempo > 90 else "slow"
            return f"**🎵 Music:** Your video tempo is {tempo:.0f} BPM ({mood}).\nSearch royalty-free music on YouTube Audio Library or Pixabay Music.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
        else: return "**🎵 Music:** Go to YouTube Audio Library or Pixabay Music, download a track, import.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["voiceover", "voice over", "narration", "dialogue"]): return "**🎙️ Voiceover:** Record with mic, or use ElevenLabs/Play.ht. Import audio.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if any(word in q for word in ["text", "subtitle", "title", "font", "kinetic"]): return "**🔤 Text:** CapCut → Text → Add Text. Type, adjust font, size. Free fonts: Google Fonts.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if "speed" in q or "slow motion" in q or "fast motion" in q: return "**⏩ Speed:** CapCut → Speed → Normal or Curve. Decrease for slow, increase for fast.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if "stabilize" in q or "shaky" in q: return "**🛠️ Stabilize:** CapCut → Stabilize (if available). Premiere Pro → Warp Stabilizer.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if "green screen" in q or "chroma key" in q: return "**🟩 Green Screen:** CapCut → Chroma Key → pick green. Premiere → Ultra Key.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    if "export" in q or "render" in q: return "**📤 Export:** CapCut → Export button → choose 1080p. Premiere → File → Export → Media → H.264.\n" + f"🎥 **Tutorial:** [YouTube]({yt_search})"
    
    return f"I couldn't find a specific answer, but here are search links:\n🔗 [Google: '{question}']({google_search})\n🔗 [YouTube: '{question}']({yt_search})\n\nTry asking about: transitions, color grading, music, text, speed, effects, overlays, green screen, export, etc."

def download_video_from_url(url, output_dir):
    """Download video using yt-dlp with Android client bypass."""
    try:
        import yt_dlp
    except ImportError:
        return None, "yt-dlp is not installed. Run `pip install yt-dlp` to enable link downloads."
    
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'mp4/best',
        'quiet': True,
        'no_warnings': True,
        # THIS IS THE BYPASS: Pretend to be an Android phone
        'extractor_args': {'youtube': {'player_client': ['android']}}, 
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            return filepath, None
    except Exception as e:
        return None, str(e)

# ---------- UI: Upload & Link Section ----------
col_upload, col_desc = st.columns([2, 1])

with col_upload:
    tab1, tab2 = st.tabs(["📁 Local File", "🔗 Remote URL"])
    
    with tab1:
        uploaded_file = st.file_uploader("", type=["mp4", "mov", "avi", "mkv"], label_visibility="collapsed")
        if uploaded_file is not None:
            # Save the uploaded file object directly to session state
            st.session_state['uploaded_file_obj'] = uploaded_file
            st.session_state['video_name'] = uploaded_file.name
            st.success("✓ File ready for analysis. Click the button below.")
    
    with tab2:
        st.warning("⚠️ YouTube blocks cloud servers. This will fail on Streamlit Cloud. Please use Local File.")
        video_url = st.text_input("", placeholder="https://youtube.com/watch?v=...", label_visibility="collapsed")
        if st.button("Fetch Video", use_container_width=True):
            if video_url:
                with st.spinner("Downloading..."):
                    temp_dir = tempfile.gettempdir()
                    filepath, error = download_video_from_url(video_url, temp_dir)
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.success(f"Downloaded: {os.path.basename(filepath)}")
                        st.session_state['video_path'] = filepath
                        st.session_state['video_name'] = os.path.basename(filepath)

with col_desc:
    st.markdown("""
    <div class="glass-card">
        <h4 style="margin:0 0 8px 0; color:#06B6D4;">Pro Analysis</h4>
        <p style="margin:0; font-size:0.85rem; color:#94A3B8; line-height: 1.5;">
            Extracts color grading, transitions, BPM, camera motion, and text overlays. Generates a step-by-step editing blueprint.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ---------- ANALYSIS TRIGGER ----------
if 'uploaded_file_obj' in st.session_state or ('video_path' in st.session_state and os.path.exists(st.session_state['video_path'])):
    st.divider()
    col_action, col_spacer = st.columns([1, 3])
    with col_action:
        if st.button("▶ Run Full Analysis", use_container_width=True):
            
            # Handle Local File Upload
            if 'uploaded_file_obj' in st.session_state:
                uploaded_file = st.session_state['uploaded_file_obj']
                temp_dir = tempfile.gettempdir()
                video_path = os.path.join(temp_dir, uploaded_file.name)
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.read())
                st.session_state['video_path'] = video_path
            
            # Retrieve path
            video_path = st.session_state['video_path']
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(value, text):
                progress_bar.progress(value)
                status_text.text(text)
            
            with st.spinner("Analyzing..."):
                results = analyze_video(video_path, update_progress)
            
            progress_bar.empty()
            status_text.empty()
            
            if results is None:
                st.error("Could not open video. Please check the file.")
            else:
                st.session_state['analysis_results'] = results
                st.rerun()

# ---------- DISPLAY RESULTS ----------
if 'analysis_results' in st.session_state:
    results = st.session_state['analysis_results']
    st.divider()
    
    if 'video_path' in st.session_state and os.path.exists(st.session_state['video_path']):
        with open(st.session_state['video_path'], "rb") as f:
            video_bytes = f.read()
        st.download_button(
            label="⬇ Download Source Video",
            data=video_bytes,
            file_name=st.session_state.get('video_name', 'video.mp4'),
            mime="video/mp4",
            use_container_width=False
        )
    
    st.subheader("Telemetry", divider=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Duration", f"{results['duration']:.1f}s")
    with col2: st.metric("Frame Rate", f"{results['fps']:.2f} fps")
    with col3: st.metric("Color Style", results['dominant_color'])
    with col4: st.metric("Camera Motion", results['camera_motion'])
    with col5:
        if results['tempo']: st.metric("Tempo (BPM)", f"{results['tempo']:.0f}")
        else: st.metric("Tempo (BPM)", "N/A")

    if results['annotated_frames']:
        st.subheader("Sample Frames", divider=True)
        cols = st.columns(min(5, len(results['annotated_frames'])))
        for i, frame in enumerate(results['annotated_frames']):
            with cols[i % len(cols)]:
                st.image(frame, caption=f"Frame {i+1}", use_container_width=True)

    if results['transitions']:
        st.subheader("Transition Analysis", divider=True)
        transition_types = [t[1] for t in results['transitions']]
        df = pd.DataFrame(transition_types, columns=["Transition"])
        st.bar_chart(df["Transition"].value_counts())
    else:
        st.info("No significant transitions detected in this clip.")

    st.subheader("Audio Profile", divider=True)
    if results['tempo']:
        mood = "Fast / Energetic" if results['tempo'] > 120 else "Moderate" if results['tempo'] > 90 else "Slow / Calm"
        st.write(f"**Mood:** {mood} ({results['tempo']:.0f} BPM)")
    if results['is_speech']: st.write("**Dialogue Detected:** Voiceover or speech present.")
    else: st.write("**Dialogue Detected:** No clear speech detected.")

    st.subheader("Editing Blueprint", divider=True)
    recommendations = get_recommendations(results)
    for rec in recommendations:
        with st.expander(rec['feature'], expanded=True):
            st.markdown("**Implementation Steps:**")
            for step in rec['steps']: st.markdown(f"- {step}")
            if rec['assets']: st.markdown(f"**Resources:** {rec['assets']}")
            if rec['ai_prompt'] != "Not applicable": st.markdown(f"**Prompt:** `{rec['ai_prompt']}`")

    report_text = f"VIDEO ANALYSIS REPORT\nDuration: {results['duration']:.1f}s\nColor: {results['dominant_color']}\nCamera: {results['camera_motion']}\n\nTRANSITIONS:\n"
    for _, ttype in results['transitions']: report_text += f"- {ttype}\n"
    report_text += "\nAUDIO:\n"
    if results['tempo']: report_text += f"Tempo: {results['tempo']:.0f} BPM\n"
    if results['is_speech']: report_text += "Speech detected.\n"
    report_text += "\nRECOMMENDATIONS:\n"
    for rec in recommendations:
        report_text += f"\n### {rec['feature']}\n"
        for step in rec['steps']: report_text += f"- {step}\n"
    
    st.download_button("📄 Export Report (.txt)", data=report_text, file_name="studio_report.txt", mime="text/plain", use_container_width=False)

# ---------- Q&A ASSISTANT ----------
st.divider()
st.subheader("Contextual Assistant")
user_question = st.chat_input("Ask about any editing technique...")
if user_question:
    with st.chat_message("user"): st.write(user_question)
    with st.chat_message("assistant"):
        results = st.session_state.get('analysis_results', None)
        answer = answer_question(user_question, results)
        st.write(answer)

# ---------- FOOTER ----------
st.markdown("""
<div class="footer">
    <span>◆ Studio Lens</span>
    <div>Built for creators · v2.0</div>
    <div style="color: #64748B;">Video Intelligence Engine</div>
</div>
""", unsafe_allow_html=True)

# ---------- DRONE MASCOT ----------
st.markdown(f"""
<div class="drone-mascot">
    <img src="{drone_src}" alt="AI Assistant" class="drone-img">
</div>
""", unsafe_allow_html=True)
