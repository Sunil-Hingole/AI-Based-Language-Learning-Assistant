import streamlit as st
import sounddevice as sd
import soundfile as sf
import tempfile
from openai import OpenAI
import speech_recognition as speech_rec  
from gtts import gTTS


# Initialize OpenAI client
client = OpenAI(api_key="API KEY")

# Session state initialization
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

def record_audio(duration=10, sample_rate=44100):
    """Record audio from microphone"""
    st.info(f"Recording for {duration} seconds... (Speak now)")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    return recording, sample_rate

def save_audio(recording, sample_rate):
    """Save recording to temporary file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    sf.write(temp_file.name, recording, sample_rate)
    return temp_file.name

def speech_to_text(audio_file, language='en-US'):
    """Convert speech to text using Google Speech Recognition"""
    recognizer = speech_rec.Recognizer() 
    with speech_rec.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language=language)
            return text
        except speech_rec.UnknownValueError:
            return "Could not understand audio"
        except speech_rec.RequestError:
            return "API unavailable"

def text_to_speech(text, language='en'):
    """Convert text to speech"""
    tts = gTTS(text=text, lang=language, slow=True)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tts.save(temp_file.name)
    return temp_file.name

def get_gpt4_feedback(text, target_language):
    """Enhanced feedback with personalized recommendations"""
    prompt = f"""
    As a {target_language} language expert, provide:
    
    1. GRAMMAR ANALYSIS:
    - Accuracy score (0-100%)
    - Specific errors found
    - Corrected version
    
    2. VOCABULARY ASSESSMENT:
    - Appropriate word choice (0-100%)
    - More natural alternatives
    
    3. PRONUNCIATION TIPS:
    - Potential trouble sounds
    - Mouth position guidance
    
    4. PERSONALIZED RECOMMENDATIONS:
    - 3 specific exercises to improve weaknesses
    - Suggested learning resources
    - Daily practice routine
    
    5. ENCOURAGEMENT:
    - Positive reinforcement
    - Progress acknowledgment
    
    For this text: "{text}"
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a supportive language coach who provides actionable feedback."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("AI Based Language Learning Assistant")
st.write("Get personalized feedback and improvement plans")

# Language selection
target_language = st.selectbox(
    "Choose language",
    options=['English', 'Spanish', 'French', 'German', 'Italian', 'Japanese', 'Chinese','Hindi'],
    index=0
)

language_codes = {
    'English': 'en-US',
    'Spanish': 'es-ES',
    'French': 'fr-FR',
    'German': 'de-DE',
    'Italian': 'it-IT',
    'Japanese': 'ja-JP',
    'Hindi': 'hi-IN',
    'Chinese': 'zh-CN'
}

# Input method
input_method = st.radio(
    "Practice method",
    options=["🎤 Speak", "⌨ Type"],
    horizontal=True,
    label_visibility="collapsed"
)

if input_method == "🎤 Speak":
    st.subheader("Voice Practice")
    duration = st.slider("Recording seconds", 5, 60, 15)
    
    if st.button(f"🎙 Record ({duration}s)"):
        audio, sample_rate = record_audio(duration)  
        audio_file = save_audio(audio, sample_rate)  
        st.audio(audio_file)
        
        text = speech_to_text(audio_file, language_codes[target_language])
        if text.lower() in ["could not understand audio", "api unavailable"]:
            st.error("Speech recognition failed. Try again.")
        else:
            st.write(f"*You:* {text}")
            with st.spinner("🔍 Analyzing..."):
                feedback = get_gpt4_feedback(text, target_language)
            st.subheader("📝 Personalized Feedback")
            st.markdown(feedback)
            
            # Generate practice exercise
            exercise_prompt = f"Create a 5-minute {target_language} practice exercise focusing on the main area needing improvement from this text: {text}"
            exercise = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": exercise_prompt}],
                temperature=0.5
            ).choices[0].message.content
            
            st.subheader("💡 Recommended Practice")
            st.markdown(exercise)

else:
    st.subheader("Text Practice")
    user_text = st.text_area("Write your text here:", height=150)
    
    if st.button("📤 Get Feedback") and user_text.strip():
        with st.spinner("🔍 Analyzing..."):
            feedback = get_gpt4_feedback(user_text, target_language)
        
        st.subheader("📝 Personalized Feedback")
        st.markdown(feedback)
        
        # Generate study plan
        plan_prompt = f"Create a 3-day study plan to improve the {target_language} skills shown in this text: {user_text}"
        study_plan = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": plan_prompt}],
            temperature=0.5
        ).choices[0].message.content
        
        st.subheader("📅 Study Plan")
        st.markdown(study_plan)

# Tips section
with st.expander("💡 Pro Tips"):
    st.write("""
    - *Shadowing Technique*: Listen to native speakers and repeat immediately after them
    - *Spaced Repetition*: Review material at increasing intervals
    - *Active Recall*: Test yourself instead of passive review
    - *Context Learning*: Learn words in full sentences, not isolation
    - *Consistency*: 20 minutes daily beats 2 hours weekly
    """)