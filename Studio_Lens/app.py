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
import shutil

try:
    import imageio_ffmpeg
except ModuleNotFoundError:
    imageio_ffmpeg = None

# ---------- PAGE CONFIG ----------
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
    drone_src = "https://cdn-icons-png.flaticon.com/512/3588/3588920.png"

# ---------- CINEMATIC DARK MODE UI ----------
st.markdown("""
<style>
    .stApp, body { background-color: #0B1120 !important; color: #F8FAFC !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stMetricValue { color: #F8FAFC !important; }
    [data-testid="stFileUploader"] {
        background-color: #1E293B !important;
        border: 2px dashed #334155 !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover { border-color: #06B6D4 !important; background-color: #0F172A !important; }
    [data-testid="stFileUploader"] label { color: #94A3B8 !important; font-weight: 500 !important; }
    .uploadedFile { background-color: #0F172A !important; color: #F8FAFC !important; border-radius: 8px !important; }
    .stTextInput input {
        background-color: #1E293B !important; color: #F8FAFC !important;
        border-radius: 12px !important; border: 1px solid #334155 !important;
    }
    .stTextInput input:focus { border-color: #06B6D4 !important; box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2) !important; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}

    .navbar {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(11, 17, 32, 0.85) !important; backdrop-filter: blur(12px);
        border-bottom: 1px solid #1E293B; padding: 0.8rem 3rem; z-index: 999;
        display: flex; justify-content: space-between; align-items: center; box-sizing: border-box;
    }
    .nav-logo { font-weight: 700; font-size: 1.3rem; letter-spacing: -0.03em; color: #F8FAFC !important; display: flex; align-items: center; gap: 8px; }
    .nav-logo span { color: #06B6D4 !important; }
    .nav-links { display: flex; gap: 2rem; align-items: center; }
    .nav-links a { text-decoration: none; color: #94A3B8 !important; font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }
    .nav-links a:hover { color: #F8FAFC !important; }
    .nav-cta { background: #1E293B; color: #06B6D4 !important; padding: 0.4rem 1.2rem; border-radius: 40px; font-weight: 600; font-size: 0.8rem; border: 1px solid #334155; }

    .hero { margin-bottom: 2rem; position: relative; z-index: 10; padding-top: 80px; }
    .hero h1 { font-size: 3.5rem; font-weight: 800; letter-spacing: -0.04em; color: #F8FAFC !important; margin-bottom: 0.5rem; line-height: 1.1; }
    .hero h1 span { background: linear-gradient(135deg, #8B5CF6, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .hero p { font-size: 1.1rem; color: #94A3B8 !important; max-width: 700px; margin-top: 0; }

    .glass-card {
        background: #1E293B; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); transition: transform 0.2s ease, box-shadow 0.2s ease; height: 100%;
    }
    .glass-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(6, 182, 212, 0.1); border-color: #06B6D4; }
    .style-card { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem; transition: all 0.3s ease; }
    .style-card:hover { border-color: #8B5CF6; transform: translateX(4px); }
    .style-title { font-size: 1.1rem; font-weight: 700; color: #06B6D4 !important; margin-bottom: 0.5rem; }
    .style-desc { font-size: 0.85rem; color: #94A3B8 !important; line-height: 1.5; }
    .resource-card { background: #1E293B; border-left: 3px solid #06B6D4; border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 0.8rem; }
    .resource-card a { color: #06B6D4 !important; text-decoration: none; font-weight: 600; }
    .resource-card a:hover { text-decoration: underline; }

    .stButton button {
        background: linear-gradient(135deg, #8B5CF6, #06B6D4) !important; color: white !important;
        border: none !important; border-radius: 12px !important; padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important; font-size: 0.9rem !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3); transition: all 0.2s ease; width: 100%;
    }
    .stButton button:hover { background: linear-gradient(135deg, #7C3AED, #0891B2) !important; transform: scale(1.02); box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5); }

    .stMetric { background: #1E293B; padding: 1.2rem !important; border-radius: 12px !important; border: 1px solid #334155; }
    .stMetric label { color: #94A3B8 !important; font-weight: 600 !important; font-size: 0.7rem !important; text-transform: uppercase !important; letter-spacing: 0.05em; }
    .stMetric .stMetricValue { color: #F8FAFC !important; font-weight: 800 !important; font-size: 1.5rem !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; background: #1E293B; border-radius: 12px; padding: 0.3rem; border: 1px solid #334155; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #94A3B8 !important; font-weight: 600; padding: 0.5rem 1.2rem; font-size: 0.85rem; }
    .stTabs [aria-selected="true"] { background: #0B1120 !important; color: #06B6D4 !important; box-shadow: 0 0 10px rgba(6, 182, 212, 0.2); }

    .streamlit-expanderHeader { background: #1E293B !important; border-radius: 8px !important; border: 1px solid #334155 !important; color: #F8FAFC !important; font-weight: 600 !important; padding: 1rem !important; }
    .streamlit-expanderHeader:hover { background: #0F172A !important; border-color: #06B6D4 !important; }
    .streamlit-expanderContent { background: #0F172A !important; border: 1px solid #334155 !important; border-top: none !important; border-radius: 0 0 8px 8px !important; padding: 1.5rem !important; }

    .stChatInput input { border: 1px solid #334155 !important; border-radius: 12px !important; padding: 0.8rem 1.5rem !important; background: #1E293B !important; color: #F8FAFC !important; }
    .stChatInput input:focus { border-color: #06B6D4 !important; box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.2) !important; }

    .footer { margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #1E293B; color: #64748B !important; font-size: 0.8rem; text-align: center; display: flex; justify-content: space-between; flex-wrap: wrap; }
    .footer span { color: #06B6D4 !important; font-weight: bold; }

    .drone-mascot { position: fixed; bottom: 20px; right: 20px; width: 120px; z-index: 10000; pointer-events: none; animation: floatDrone 4s ease-in-out infinite alternate; mix-blend-mode: screen; filter: drop-shadow(0 10px 10px rgba(0,0,0,0.5)); }
    @keyframes floatDrone { 0% { transform: translateY(0px) rotate(-3deg); } 100% { transform: translateY(-15px) rotate(3deg); } }
    .drone-img { width: 100%; height: auto; display: block; }
    .badge { display: inline-block; padding: 0.2rem 0.7rem; background: rgba(6, 182, 212, 0.15); color: #06B6D4 !important; border-radius: 20px; font-size: 0.7rem; font-weight: 600; margin-right: 0.4rem; margin-bottom: 0.4rem; }
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

# ---- HERO ----
st.markdown("""
<div class="hero">
    <h1>Video Intelligence <span>Studio Lens</span></h1>
    <p>Upload a video or paste a link to automatically decode its editing DNA — color grading, transitions, audio structure, and motion patterns.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# BACKEND FUNCTIONS
# ============================================================

def extract_audio(video_path):
    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, "temp_audio.wav")
    ffmpeg_exe = None
    try:
        if imageio_ffmpeg is not None:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_exe = None
    if not ffmpeg_exe:
        ffmpeg_exe = shutil.which("ffmpeg")
    if not ffmpeg_exe:
        return None
    try:
        subprocess.run(
            [ffmpeg_exe, '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
             '-ar', '44100', '-ac', '2', audio_path, '-y'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
    except Exception:
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
    results['avg_brightness'] = float(np.mean(brightness_list))
    results['avg_contrast'] = float(np.mean(contrast_list))

    if progress_callback: progress_callback(0.75, "Detecting text...")
    sample_frames_for_text = color_frames[::max(1, len(color_frames)//5)]
    text_present_frames = sum(1 for frame in sample_frames_for_text if detect_text_presence(frame))
    results['text_overlay'] = text_present_frames > (len(sample_frames_for_text) // 2)

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
    if audio_path and os.path.exists(audio_path):
        try: os.remove(audio_path)
        except Exception: pass

    if progress_callback: progress_callback(1.0, "Done!")
    return results

def get_recommendations(results):
    recs = []
    color = results['dominant_color']
    if color == "Teal & Orange":
        recs.append({"feature": "Teal & Orange Color Grade", "steps": ["Open **CapCut** (free) – [Download](https://www.capcut.com/)", "Import your video: tap 'New project' → select video.", "Tap the clip → **Filters** → search 'Teal Orange'.", "Apply filter, adjust strength.", "In **DaVinci Resolve** – [Download](https://www.blackmagicdesign.com/products/davinciresolve)", "Go to **Color** page → use **Color Wheels**: shadows to blue, highlights to orange.", "Free LUTs: [freeluts.com](https://www.freeluts.com/)"], "assets": "No extra assets needed.", "ai_prompt": "AI prompt: 'Cinematic teal and orange color graded scene, high contrast, film look'"})
    elif color == "Sepia / Vintage":
        recs.append({"feature": "Sepia / Vintage Look", "steps": ["Open **CapCut** – [Download](https://www.capcut.com/)", "Import video, tap clip → **Filters** → search 'Sepia' or 'Vintage'.", "Apply filter.", "For film grain: search 'free film grain overlay' on YouTube, download, place over clip, blend mode **Overlay** or **Screen**."], "assets": "Film grain: [YouTube search](https://www.youtube.com/results?search_query=free+film+grain+overlay)", "ai_prompt": "AI prompt: 'Old vintage sepia film look, scratches, warm tones'"})
    elif color == "Black & White":
        recs.append({"feature": "Black & White", "steps": ["Set Saturation to 0: CapCut → clip → **Adjust** → **Saturation** → 0.", "Or apply 'Black & White' filter from **Filters**."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'High contrast black and white cinematic shot'"})
    elif color == "Warm":
        recs.append({"feature": "Warm Color Tone", "steps": ["In CapCut: clip → **Adjust** → **Temperature** → move slider right (+20)."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'Warm sunset lighting, golden hour, cozy atmosphere'"})
    elif color == "Cool":
        recs.append({"feature": "Cool Color Tone", "steps": ["In CapCut: clip → **Adjust** → **Temperature** → move slider left (-20)."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'Cool blue moonlight, icy tones, calm mood'"})

    if results.get('avg_contrast', 0) > 70:
        recs.append({"feature": "High Contrast", "steps": ["Increase contrast: clip → **Adjust** → **Contrast** → +30."], "assets": "No assets needed.", "ai_prompt": "AI prompt: 'High contrast dramatic lighting, deep shadows, bright highlights'"})
    elif results.get('avg_contrast', 0) < 40:
        recs.append({"feature": "Low Contrast (Soft Look)", "steps": ["Decrease contrast: clip → **Adjust** → **Contrast** → -30."], "assets": "Optional: add slight blur or diffusion.", "ai_prompt": "AI prompt: 'Soft low contrast dreamy look, pastel colors'"})

    if results.get('transitions'):
        transition_counts = {}
        for _, ttype in results['transitions']:
            transition_counts[ttype] = transition_counts.get(ttype, 0) + 1
        for ttype in transition_counts:
            if ttype == "Cut":
                recs.append({"feature": "Cuts", "steps": ["Place clips next to each other with no transition."], "assets": "No assets needed.", "ai_prompt": "Not applicable"})
            elif "Fade" in ttype:
                recs.append({"feature": "Fade Transitions", "steps": ["In CapCut: tap transition box → choose 'Fade' or 'Dissolve'. Adjust duration."], "assets": "Built-in transitions.", "ai_prompt": "Not applicable"})
            elif "Zoom" in ttype:
                recs.append({"feature": "Zoom Transitions", "steps": ["In CapCut: transition box → search 'Zoom' → apply."], "assets": "Built-in transitions.", "ai_prompt": "Not applicable"})
            elif "Slide" in ttype:
                recs.append({"feature": "Slide / Pan Transitions", "steps": ["In CapCut: transition box → search 'Slide'. Or keyframe position."], "assets": "Built-in transitions.", "ai_prompt": "Not applicable"})

    if results.get('camera_motion') and results['camera_motion'] != "Static":
        recs.append({"feature": f"Camera Movement: {results['camera_motion']}", "steps": ["To recreate: use gimbal or steady hand when filming.", "Or add digital movement: keyframe Position/Scale in editor."], "assets": "No assets needed.", "ai_prompt": "Not applicable"})

    if results.get('text_overlay'):
        recs.append({"feature": "Text Overlay Detected", "steps": ["Add text: CapCut → **Text** → **Add Text**.", "Type text, adjust font, size, color.", "Premiere Pro: use Type Tool (T)."], "assets": "Free fonts: [Google Fonts](https://fonts.google.com/)", "ai_prompt": "Not applicable"})

    if results.get('tempo'):
        tempo = results['tempo']
        mood = "fast / energetic" if tempo > 120 else "moderate" if tempo > 90 else "slow / calm"
        recs.append({"feature": f"Music ({mood}, {tempo:.0f} BPM)", "steps": ["Go to free music sites: [YouTube Audio Library](https://www.youtube.com/audiolibrary), [Pixabay Music](https://pixabay.com/music/).", f"Search for '{mood} music {tempo:.0f} BPM'.", "Download and import into editor."], "assets": f"Search: 'royalty free {mood} music {tempo:.0f} BPM'", "ai_prompt": f"AI prompt: 'Upbeat electronic track at {tempo:.0f} BPM, energetic'"})

    if results.get('is_speech'):
        recs.append({"feature": "Voiceover / Dialogue", "steps": ["Record with microphone, or use AI voice: [ElevenLabs](https://elevenlabs.io/), [Play.ht](https://play.ht/).", "Import and place on audio track."], "assets": "AI voices: ElevenLabs, Play.ht", "ai_prompt": "AI prompt: 'Professional voice, confident, explaining product, 30 seconds'"})

    return recs

# ---------- Link Inspector & Downloader ----------
def get_link_info(url):
    try:
        import yt_dlp
    except ImportError:
        return None, "yt-dlp is not installed."
    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True, 'socket_timeout': 15, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info: return None, "Could not extract information."
            return {
                'title': info.get('title', 'Unknown Title'),
                'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                'duration': info.get('duration', 0) or 0,
                'view_count': info.get('view_count', 0) or 0,
                'thumbnail': info.get('thumbnail', ''),
                'extractor': info.get('extractor', 'Unknown'),
            }, None
    except Exception as e:
        return None, str(e)

def download_video_from_url(url, output_dir):
    try:
        import yt_dlp
    except ImportError:
        return None, "yt-dlp is not installed."

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'bv*+ba/b',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['tv', 'android', 'web_safari'], 'player_skip': ['webpage']}},
        'impersonate': 'chrome',
        'source_address': '0.0.0.0',
        'nocheckcertificate': True,
        'geo_bypass': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info: return None, "Failed to extract video info."
            filepath = ydl.prepare_filename(info)
            if not filepath: return None, "Failed to determine filename."
            return filepath, None
    except Exception as e:
        return None, str(e)

# ---------- AI Assistant ----------
def answer_question(question, results=None):
    q = question.lower().strip()
    yt_search = f"https://www.youtube.com/results?search_query={question.replace(' ', '+')}"
    google_search = f"https://www.google.com/search?q={question.replace(' ', '+')}"

    if any(w in q for w in ["star", "sparkle", "glitter", "particle", "magic"]):
        return "**✨ Star / Sparkle / Particle Effects:**\n\n1. Open **CapCut** → tap clip → **Overlays** or **Effects**.\n2. Search for 'stars', 'sparkles', 'particles'.\n3. Drag it over your video, adjust size.\n4. Set blend mode to **Screen** or **Add**.\n\n" + f"🎥 [YouTube Tutorial]({yt_search}) | 🔎 [Google]({google_search})"
    if any(w in q for w in ["overlay", "light leak", "bokeh", "dust"]):
        return "**🎞️ Overlay Effects:**\n\n1. Download free overlays from [Pexels](https://www.pexels.com/search/videos/overlay/) or [Pixabay](https://pixabay.com/videos/search/overlay/).\n2. Place on track above main video.\n3. Blend mode → **Screen**.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["intro", "outro", "opening"]):
        return "**🎬 Intro / Outro:**\n\n1. CapCut → **Effects** → search 'Intro'.\n2. Or use **Canva** for templates: [canva.com](https://www.canva.com/).\n3. Use **Text Animation** for titles.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["fade", "dissolve"]):
        return "**🌑 Fade Transition:**\nIn CapCut: tap the square between clips → choose 'Fade' or 'Dissolve'.\n\n" + f"🎥 [YouTube]({yt_search})"
    if "cut" in q and "transition" in q:
        return "**✂️ Cut Transition:**\nJust place clips next to each other with no gap.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["zoom transition", "zoom in", "zoom out"]):
        return "**🔍 Zoom Transition:**\nCapCut: transition box → 'Zoom'. Or keyframe scale in Premiere Pro.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["slide", "whip", "pan transition"]):
        return "**↔️ Slide / Whip Transition:**\nCapCut: transition box → search 'Slide' or 'Whip'.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["glitch", "rgb"]):
        return "**📺 Glitch Transition:**\nCapCut: search 'Glitch' in transitions.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["teal", "orange", "color grade", "cinematic", "lut"]):
        return "**🎨 Teal & Orange:**\nCapCut: Filters → 'Teal Orange'. Or DaVinci Color Wheels. Free LUTs: [freeluts.com](https://www.freeluts.com/).\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["sepia", "vintage", "retro"]):
        return "**📜 Sepia/Vintage:**\nCapCut: Filters → 'Sepia'. Add film grain overlay.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["black and white", "b&w", "monochrome"]):
        return "**⬛ Black & White:**\nSet Saturation to 0, or apply B&W filter.\n\n" + f"🎥 [YouTube]({yt_search})"
    if "contrast" in q:
        return "**🌗 Contrast:**\nCapCut: Adjust → Contrast.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["music", "audio", "bpm"]):
        if results and results.get('tempo'):
            tempo = results['tempo']
            mood = "fast" if tempo > 120 else "moderate" if tempo > 90 else "slow"
            return f"**🎵 Music:** Your video is {tempo:.0f} BPM ({mood}).\nSearch [YouTube Audio Library](https://www.youtube.com/audiolibrary) or [Pixabay Music](https://pixabay.com/music/).\n\n" + f"🎥 [YouTube]({yt_search})"
        return "**🎵 Music:** [YouTube Audio Library](https://www.youtube.com/audiolibrary) or [Pixabay Music](https://pixabay.com/music/).\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["voiceover", "narration", "dialogue"]):
        return "**🎙️ Voiceover:** Use [ElevenLabs](https://elevenlabs.io/) or [Play.ht](https://play.ht/).\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["text", "subtitle", "title", "font", "kinetic"]):
        return "**🔤 Text:** CapCut → Text → Add Text. Free fonts: [Google Fonts](https://fonts.google.com/).\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["speed", "slow motion", "fast motion"]):
        return "**⏩ Speed:** CapCut → Speed → Normal or Curve.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["stabilize", "shaky"]):
        return "**🛠️ Stabilize:** CapCut → Stabilize. Premiere Pro → Warp Stabilizer.\n\n" + f"🎥 [YouTube]({yt_search})"
    if "green screen" in q or "chroma key" in q:
        return "**🟩 Green Screen:** CapCut → Chroma Key → pick green.\n\n" + f"🎥 [YouTube]({yt_search})"
    if any(w in q for w in ["export", "render"]):
        return "**📤 Export:** CapCut → 1080p. Premiere → File → Export → H.264.\n\n" + f"🎥 [YouTube]({yt_search})"

    return f"I couldn't find a specific answer, but here are search links:\n🔗 [Google]({google_search})\n🔗 [YouTube]({yt_search})\n\nTry asking about: transitions, color grading, music, text, speed, effects, overlays, green screen, export."

# ============================================================
# UI: TABS
# ============================================================

st.markdown("<div style='padding-top: 20px;'></div>", unsafe_allow_html=True)

tab_analysis, tab_url, tab_styles, tab_resources = st.tabs([
    "📁 Local Analysis",
    "🔗 Remote URL Analysis",
    "🎨 Style Library",
    "📚 Resource Hub"
])

# ============================================================
# TAB 1: LOCAL FILE ANALYSIS
# ============================================================
with tab_analysis:
    col_upload, col_desc = st.columns([2, 1])
    with col_upload:
        uploaded_file = st.file_uploader("Upload a video to analyze", type=["mp4", "mov", "avi", "mkv"], label_visibility="collapsed")
        if uploaded_file is not None:
            st.session_state['uploaded_file_obj'] = uploaded_file
            st.session_state['video_name'] = uploaded_file.name
            st.success("✓ File ready. Click 'Run Full Analysis' below.")
    with col_desc:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin:0 0 8px 0; color:#06B6D4;">Pro Analysis</h4>
            <p style="margin:0; font-size:0.85rem; color:#94A3B8; line-height: 1.5;">
                Extracts color grading, transitions, BPM, camera motion, and text overlays. Generates a step-by-step editing blueprint.
            </p>
        </div>
        """, unsafe_allow_html=True)

    if 'uploaded_file_obj' in st.session_state:
        st.divider()
        col_action, col_spacer = st.columns([1, 3])
        with col_action:
            if st.button("▶ Run Full Analysis", key="run_local"):
                uploaded_file = st.session_state['uploaded_file_obj']
                temp_dir = tempfile.gettempdir()
                video_path = os.path.join(temp_dir, uploaded_file.name)
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.read())
                st.session_state['video_path'] = video_path
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
                    st.error("Could not open video. Please try a different file.")
                else:
                    st.session_state['analysis_results'] = results
                    st.rerun()

# ============================================================
# TAB 2: REMOTE URL ANALYSIS
# ============================================================
with tab_url:
    st.markdown("### 🔗 Analyze a Video from a URL")
    st.markdown("Paste a direct video link (Vimeo, Twitter, TikTok, direct MP4, etc.). We'll download it and run the full analysis, just like the Local File tab.")
    
    st.warning("⚠️ **Note on YouTube:** YouTube aggressively blocks cloud servers (like Streamlit). If YouTube fails, please download the video to your computer and use the **Local Analysis** tab instead. Other platforms will work perfectly.")

    video_url = st.text_input("Video URL", placeholder="https://vimeo.com/... or https://example.com/video.mp4", label_visibility="collapsed", key="url_input")

    if st.button("⬇ Download and Analyze", key="run_url"):
        if not video_url:
            st.warning("Please paste a link first.")
        else:
            # Check if it's a YouTube link
            is_youtube = "youtube.com" in video_url or "youtu.be" in video_url
            
            if is_youtube:
                st.info("🔍 YouTube detected. Fetching metadata (inspection only)...")
                info, error = get_link_info(video_url)
                if error:
                    st.error(f"YouTube blocked the request: {error}")
                    st.info("💡 **Solution:** Please download the video to your computer and use the **Local Analysis** tab for the full frame-by-frame breakdown.")
                else:
                    st.success("✓ Metadata extracted!")
                    col_thumb, col_info = st.columns([1, 2])
                    with col_thumb:
                        if info['thumbnail']:
                            st.image(info['thumbnail'], use_container_width=True)
                    with col_info:
                        st.markdown(f"### {info['title']}")
                        st.markdown(f"**Channel:** {info['uploader']}")
                        duration_str = f"{int(info['duration'] // 60)}m {int(info['duration'] % 60)}s" if info['duration'] else "N/A"
                        st.markdown(f"**Duration:** {duration_str}")
                        st.markdown(f"**Views:** {info['view_count']:,}" if info['view_count'] else "**Views:** N/A")
                    
                    st.divider()
                    st.markdown("### 💡 What to Look For in This Video")
                    st.markdown("""
                    - **Color Grading:** Warm, cool, or cinematic tone? Look at shadows vs. highlights.
                    - **Transitions:** Hard cuts, fades, zooms, or slides?
                    - **Camera Motion:** Static, panning, tilting, or gimbal movement?
                    - **Text Overlays:** Titles, subtitles, or kinetic typography?
                    - **Music & Audio:** Fast, slow, or moderate? Voiceover or dialogue?
                    - **Pacing:** Fast-paced or slow and deliberate?
                    """)
                    st.info("💡 **To get the full automated frame analysis:** Download this video to your computer and upload it in the **Local Analysis** tab.")
            else:
                # Non-YouTube URL: attempt download and full analysis
                temp_dir = tempfile.gettempdir()
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("Downloading video...")
                progress_bar.progress(0.1)

                filepath, error = download_video_from_url(video_url, temp_dir)

                if error:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Download failed: {error}")
                elif filepath is None:
                    progress_bar.empty()
                    status_text.empty()
                    st.error("Download failed silently. Please check the URL.")
                else:
                    st.success(f"✓ Downloaded: {os.path.basename(filepath)}")
                    st.session_state['video_path'] = filepath
                    st.session_state['video_name'] = os.path.basename(filepath)

                    def update_progress(value, text):
                        progress_bar.progress(value)
                        status_text.text(text)

                    with st.spinner("Analyzing..."):
                        results = analyze_video(filepath, update_progress)

                    progress_bar.empty()
                    status_text.empty()

                    if results is None:
                        st.error("Could not analyze the downloaded video.")
                    else:
                        st.session_state['analysis_results'] = results
                        st.rerun()

# ============================================================
# RESULTS DISPLAY (Shared by both tabs)
# ============================================================
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
            mime="video/mp4"
        )

    st.subheader("📊 Telemetry", divider=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Duration", f"{results['duration']:.1f}s")
    with col2: st.metric("Frame Rate", f"{results['fps']:.2f} fps")
    with col3: st.metric("Color Style", results['dominant_color'])
    with col4: st.metric("Camera Motion", results['camera_motion'])
    with col5:
        if results['tempo']: st.metric("Tempo (BPM)", f"{results['tempo']:.0f}")
        else: st.metric("Tempo (BPM)", "N/A")

    if results['annotated_frames']:
        st.subheader("🖼️ Sample Frames", divider=True)
        cols = st.columns(min(5, len(results['annotated_frames'])))
        for i, frame in enumerate(results['annotated_frames']):
            with cols[i % len(cols)]:
                st.image(frame, caption=f"Frame {i+1}", use_container_width=True)

    if results['transitions']:
        st.subheader("🎬 Transition Analysis", divider=True)
        transition_types = [t[1] for t in results['transitions']]
        df = pd.DataFrame(transition_types, columns=["Transition"])
        st.bar_chart(df["Transition"].value_counts())
    else:
        st.info("No significant transitions detected in this clip.")

    st.subheader("🎵 Audio Profile", divider=True)
    if results['tempo']:
        mood = "Fast / Energetic" if results['tempo'] > 120 else "Moderate" if results['tempo'] > 90 else "Slow / Calm"
        st.write(f"**Mood:** {mood} ({results['tempo']:.0f} BPM)")
    st.write(f"**Dialogue Detected:** {'Yes' if results['is_speech'] else 'No clear speech detected.'}")

    st.subheader("✏️ Editing Blueprint", divider=True)
    recommendations = get_recommendations(results)
    for rec in recommendations:
        with st.expander(rec['feature'], expanded=True):
            st.markdown("**Implementation Steps:**")
            for step in rec['steps']:
                st.markdown(f"- {step}")
            if rec['assets']:
                st.markdown(f"**Resources:** {rec['assets']}")
            if rec['ai_prompt'] != "Not applicable":
                st.markdown(f"**Prompt:** `{rec['ai_prompt']}`")

    report_text = f"VIDEO ANALYSIS REPORT\n{'='*40}\nDuration: {results['duration']:.1f}s\nFPS: {results['fps']:.2f}\nColor: {results['dominant_color']}\nCamera: {results['camera_motion']}\n\nTRANSITIONS:\n"
    for _, ttype in results['transitions']:
        report_text += f"- {ttype}\n"
    report_text += "\nAUDIO:\n"
    if results['tempo']:
        report_text += f"Tempo: {results['tempo']:.0f} BPM\n"
    if results['is_speech']:
        report_text += "Speech detected.\n"
    report_text += "\nRECOMMENDATIONS:\n"
    for rec in recommendations:
        report_text += f"\n### {rec['feature']}\n"
        for step in rec['steps']:
            report_text += f"- {step}\n"

    st.download_button("📄 Export Report (.txt)", data=report_text, file_name="studio_report.txt", mime="text/plain")

# ============================================================
# TAB 3: STYLE LIBRARY
# ============================================================
with tab_styles:
    st.markdown("### 🎨 Color Grading Style Library")
    st.markdown("Explore popular video editing styles with step-by-step instructions for **CapCut** (free) and **DaVinci Resolve** (free).")

    style_data = [
        {"name": "🎬 Teal & Orange (Hollywood Look)", "desc": "The classic cinematic blockbuster look. Cool shadows + warm highlights.", "best_for": "Action, Cinematic, Trailer", "steps": "In CapCut: Filters → search 'Teal Orange' → apply at 70% strength.\nIn DaVinci: Color Wheels → Shadows to cyan-blue, Highlights to orange."},
        {"name": "🌅 Warm Golden Hour", "desc": "Golden sunset tones, cozy and inviting. Perfect for travel and lifestyle content.", "best_for": "Travel, Vlog, Lifestyle", "steps": "In CapCut: Adjust → Temperature +25, Tint +10, Saturation +10.\nAdd a subtle 'Sunburst' filter."},
        {"name": "🌙 Cool Cinematic Blue", "desc": "Moody, atmospheric, and dramatic. Great for sci-fi, thriller, or introspective content.", "best_for": "Sci-Fi, Thriller, Drama", "steps": "In CapCut: Adjust → Temperature -20, Contrast +15.\nFilters → search 'Cinematic Blue' or 'Moody'."},
        {"name": "📜 Vintage / Sepia Film", "desc": "Old-school film look with warm tones, grain, and faded blacks.", "best_for": "Nostalgia, Documentary, Artistic", "steps": "In CapCut: Filters → 'Sepia' or 'Vintage'.\nAdd film grain overlay (search 'free film grain' on YouTube) with Screen blend mode at 30% opacity."},
        {"name": "⬛ High Contrast B&W", "desc": "Bold, dramatic, and timeless. Great for portraits, fashion, and dramatic storytelling.", "best_for": "Portrait, Fashion, Drama", "steps": "In CapCut: Adjust → Saturation 0, Contrast +40, Brightness -5."},
        {"name": "🌈 Pastel Dreamy", "desc": "Soft, airy, and whimsical. Popular in beauty, lifestyle, and romantic content.", "best_for": "Beauty, Romance, Lifestyle", "steps": "In CapCut: Filters → search 'Pastel' or 'Dreamy'.\nAdjust → Saturation +5, Contrast -10, Brightness +10."},
        {"name": "⚡ Cyberpunk Neon", "desc": "Vibrant purples, pinks, and blues. High saturation and glow effects.", "best_for": "Tech, Music Videos, Futuristic", "steps": "In CapCut: Filters → 'Neon' or 'Cyberpunk'.\nAdd glow effect (Effects → 'Glow') at 40%."},
        {"name": "🎞️ Film Emulation", "desc": "Mimics the look of Kodak Portra, Fuji, or CineStill film stocks.", "best_for": "Portrait, Weddings, Artistic", "steps": "In CapCut: Filters → 'Film' → try 'Kodak' or 'Fuji'.\nAdd subtle grain overlay at 20% opacity."}
    ]

    for style in style_data:
        st.markdown(f"""
        <div class="style-card">
            <div class="style-title">{style['name']}</div>
            <div class="style-desc">{style['desc']}</div>
            <div style="margin-top: 0.8rem;"><span class="badge">Best for: {style['best_for']}</span></div>
            <div style="margin-top: 0.8rem; font-size: 0.8rem; color: #CBD5E1; white-space: pre-line; line-height: 1.6;">
                <strong style="color:#06B6D4;">How to:</strong> {style['steps']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# TAB 4: RESOURCE HUB
# ============================================================
with tab_resources:
    st.markdown("### 📚 Free Creator Resource Hub")
    st.markdown("Handpicked, 100% free resources for every part of your video editing workflow.")

    st.markdown("#### 🎵 Music & Audio")
    st.markdown("""
    <div class="resource-card"><a href="https://www.youtube.com/audiolibrary" target="_blank">YouTube Audio Library</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Royalty-free music and sound effects.</p></div>
    <div class="resource-card"><a href="https://pixabay.com/music/" target="_blank">Pixabay Music</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Free music with no attribution required.</p></div>
    <div class="resource-card"><a href="https://freesound.org/" target="_blank">Freesound.org</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Creative Commons licensed sound effects.</p></div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎨 Color LUTs & Grading")
    st.markdown("""
    <div class="resource-card"><a href="https://www.freeluts.com/" target="_blank">FreeLUTs.com</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Hundreds of free LUTs for cinematic color grading.</p></div>
    <div class="resource-card"><a href="https://groundcontrol.film/" target="_blank">Ground Control</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Premium-quality free film emulation LUTs.</p></div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎞️ Video Overlays & Stock")
    st.markdown("""
    <div class="resource-card"><a href="https://www.pexels.com/videos/" target="_blank">Pexels Videos</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Free HD stock video footage.</p></div>
    <div class="resource-card"><a href="https://mixkit.co/free-stock-video/" target="_blank">Mixkit</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Free HD videos, music, and templates.</p></div>
    <div class="resource-card"><a href="https://pixabay.com/videos/" target="_blank">Pixabay Videos</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Free stock videos and overlays.</p></div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🔤 Fonts & Typography")
    st.markdown("""
    <div class="resource-card"><a href="https://fonts.google.com/" target="_blank">Google Fonts</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Over 1,500 free, open-source fonts.</p></div>
    <div class="resource-card"><a href="https://www.dafont.com/" target="_blank">DaFont</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Thousands of free fonts including display and decorative.</p></div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎙️ AI Voice & Narration")
    st.markdown("""
    <div class="resource-card"><a href="https://elevenlabs.io/" target="_blank">ElevenLabs</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">Realistic AI voices for voiceovers. Free tier.</p></div>
    <div class="resource-card"><a href="https://play.ht/" target="_blank">Play.ht</a><p style="margin:0.3rem 0 0 0; font-size:0.85rem; color:#94A3B8;">AI voice generator with multiple languages.</p></div>
    """, unsafe_allow_html=True)

# ============================================================
# CONTEXTUAL ASSISTANT
# ============================================================
st.divider()
st.subheader("🤖 Contextual Assistant")
st.markdown("Ask about any editing technique — transitions, color grading, music, text, effects, and more.")
user_question = st.chat_input("Ask about any editing technique...")
if user_question:
    with st.chat_message("user"):
        st.write(user_question)
    with st.chat_message("assistant"):
        results = st.session_state.get('analysis_results', None)
        answer = answer_question(user_question, results)
        st.write(answer)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    <span>◆ Studio Lens</span>
    <div>Built for creators · v3.0</div>
    <div style="color: #64748B;">Video Intelligence Engine</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# DRONE MASCOT
# ============================================================
st.markdown(f"""
<div class="drone-mascot">
    <img src="{drone_src}" alt="AI Assistant" class="drone-img">
</div>
""", unsafe_allow_html=True)
