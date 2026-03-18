import os
import base64
import requests
import io
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv
import math

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

SARVAM_API_URL = "https://api.sarvam.ai/text-to-speech"


class AudioChunk:
    def __init__(self, chunk_id: str, title: str, title_te: str, text: str, 
                 text_te: str, category: str = "general"):
        self.chunk_id = chunk_id
        self.title = title
        self.title_te = title_te
        self.text = text
        self.text_te = text_te
        self.category = category
        self.audio_url_en = None
        self.audio_url_te = None
    
    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "title": self.title,
            "title_te": self.title_te,
            "text": self.text,
            "text_te": self.text_te,
            "category": self.category,
            "audio_url_en": self.audio_url_en,
            "audio_url_te": self.audio_url_te
        }


def _convert_formula_to_speech(formula: str) -> str:
    if not formula:
        return formula
    return (formula
            .replace('θ', 'theta')
            .replace('²', ' squared')
            .replace('³', ' cubed')
            .replace('*', ' multiplied by ')
            .replace('/', ' divided by ')
            .replace('+', ' plus ')
            .replace('-', ' minus ')
            .replace('=', ' equals ')
            .replace('(', ' open parenthesis ')
            .replace(')', ' close parenthesis '))


def get_api_key():
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        print("SARVAM_API_KEY not found. Please add SARVAM_API_KEY to your .env file.")
        print("Get your API key from: https://dashboard.sarvam.ai")
    return api_key


def generate_explanation_text(angle: float, velocity: float, gravity: float, 
                                prev_angle: Optional[float] = None, prev_velocity: Optional[float] = None, 
                                prev_gravity: Optional[float] = None,
                                custom_formula: Optional[str] = None,
                                include_formula: bool = False) -> str:
    parts = []
    
    if include_formula and custom_formula:
        formula_speech = _convert_formula_to_speech(custom_formula)
        parts.append(f"The projectile motion formula being used is: {formula_speech}. ")
        parts.append("This formula describes the relationship between the sideways distance, vertical height, launch angle, initial velocity, and gravity. ")
        parts.append("In this formula, y represents the vertical height, x represents the sideways distance, theta represents the launch angle, v represents the initial velocity, and g represents gravitational acceleration. ")
    
    parts.append(f"In this projectile motion simulation, the projectile is launched at an angle of {angle} degrees with an initial velocity of {velocity} meters per second under a gravitational acceleration of {gravity} meters per second squared.")
    
    if prev_angle is not None and prev_angle != angle:
        change = angle - prev_angle
        direction = "increased" if change > 0 else "decreased"
        parts.append(f"The launch angle has {direction} from {prev_angle} to {angle} degrees. ")
        if angle > prev_angle:
            parts.append(f"A higher angle means the projectile reaches a greater maximum height but travels a shorter distance. ")
        else:
            parts.append(f"A lower angle means the projectile travels farther but reaches a lower maximum height. ")
    
    if prev_velocity is not None and prev_velocity != velocity:
        change = velocity - prev_velocity
        direction = "increased" if change > 0 else "decreased"
        parts.append(f"The initial velocity has {direction} from {prev_velocity} to {velocity} meters per second. ")
        if velocity > prev_velocity:
            parts.append(f"Higher velocity means the projectile travels faster and reaches further. ")
        else:
            parts.append(f"Lower velocity means the projectile travels slower and doesn't go as far. ")
    
    if prev_gravity is not None and prev_gravity != gravity:
        change = gravity - prev_gravity
        direction = "increased" if change > 0 else "decreased"
        parts.append(f"The gravitational acceleration has {direction} from {prev_gravity} to {gravity} meters per second squared. ")
        if gravity > prev_gravity:
            parts.append(f"Stronger gravity pulls the projectile down faster, reducing both the flight time and the maximum height. ")
        else:
            parts.append(f"Weaker gravity lets the projectile stay in the air longer and reach a higher maximum height. ")
    
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from physics_service import calculate_trajectory
    result = calculate_trajectory(angle, velocity, gravity)
    
    parts.append(f"The maximum height reached is {result['max_height']} meters. ")
    parts.append(f"The total range or distance covered is {result['range']} meters. ")
    parts.append(f"The projectile remains in the air for {result['time_of_flight']} seconds.")
    
    return " ".join(parts)


def synthesize_speech(text: str, target_language_code: str = "en-IN", 
                      speaker: str = "arya") -> dict:
    api_key = get_api_key()
    
    if not api_key:
        return {"error": "API key missing", "audio_url": None}
    
    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": [text],
        "target_language_code": target_language_code,
        "speaker": "shruti",
        "model": "bulbul:v3",
        "speech_sample_rate": 16000
    }
    
    try:
        response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("audios") and len(result["audios"]) > 0:
            audio_base64 = result["audios"][0]
            if not audio_base64 or len(audio_base64) < 1000:
                print(f"Warning: Suspiciously short audio data for text: {text[:50]}...")
                return {"error": "Audio data too short", "audio_url": None}
            audio_data_url = f"data:audio/wav;base64,{audio_base64}"
            return {
                "audio_url": audio_data_url,
                "request_id": result.get("request_id")
            }
        else:
            print(f"Warning: No audio returned from API for text: {text[:50]}...")
            return {"error": "No audio returned from API", "audio_url": None}
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling Sarvam API: {e}")
        return {"error": str(e), "audio_url": None}
    except Exception as e:
        print(f"Unexpected error in synthesize_speech: {e}")
        return {"error": str(e), "audio_url": None}


def get_audio_stream(text: str):
    result = synthesize_speech(text)
    return result.get("audio_url")


def generate_explanation_text_telugu(angle: float, velocity: float, gravity: float, 
                                    prev_angle: Optional[float] = None, prev_velocity: Optional[float] = None, 
                                    prev_gravity: Optional[float] = None,
                                    custom_formula: Optional[str] = None,
                                    include_formula: bool = False) -> str:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from physics_service import calculate_trajectory
    result = calculate_trajectory(angle, velocity, gravity)
    
    parts = []
    
    angle_rad = angle * math.pi / 180
    
    if include_formula and custom_formula:
        formula_speech = _convert_formula_to_speech(custom_formula)
        parts.append(f"Formula: {formula_speech}. ")
    
    parts.append(f"Hello everyone! Niiku projectile motion ni explanation ivvutu. ")
    parts.append(f"Ipudu i simulation lo, projectile {angle} degrees angle daari, {velocity} m/s velocity tho launch avutundi. ")
    parts.append(f"Ekkada velocity ni two components lo split cheyyali. Sideways component = {velocity * math.cos(angle_rad):.2f} m/s. Vertical component = {velocity * math.sin(angle_rad):.2f} m/s. ")
    parts.append(f"Regarding sideways motion, gravity effect ledu. Kabbati constant velocity tho move avutundi. Formula: x = v cos theta times t. ")
    parts.append(f"Vertical motion lo, gravity {gravity} m/s² impact undi. Upward movement lo velocity decrease avutundi, downward movement lo increase avutundi. Formula: y = v sinθ × t - ½gt². ")
    
    parts.append(f"\nOkay, ante results: ")
    parts.append(f"Maximum height = {result['max_height']:.2f} meters. ")
    parts.append(f"Total range = {result['range']:.2f} meters. ")
    parts.append(f"Time of flight = {result['time_of_flight']:.2f} seconds. ")
    
    if prev_angle is not None and prev_angle != angle:
        diff = angle - prev_angle
        if diff > 0:
            parts.append(f"\nSo, angle increase ayyindi ante, vertical component increase avutundi. Sideways component decrease avutundi. ")
            parts.append(f"Kabbati maximum height increase avutundi. Range decrease avutundi. ")
            parts.append(f"Remember: 45° max range ki ideal angle. ")
        else:
            parts.append(f"\nSo, angle decrease ayyindi ante, sideways component increase avutundi. Vertical component decrease avutundi. ")
            parts.append(f"Kabbati range increase avutundi. Maximum height decrease avutundi. ")
    
    if prev_velocity is not None and prev_velocity != velocity:
        diff = velocity - prev_velocity
        if diff > 0:
            parts.append(f"\nVelocity increase ayyindi ante, initial energy increase avutundi. ")
            parts.append(f"Both height and range increase avutundi. Physics ante, Range ∝ v² and Height ∝ v². ")
        else:
            parts.append(f"\nVelocity decrease ayyindi ante, initial energy decrease avutundi. ")
            parts.append(f"Both height and range decrease avutundi. ")
    
    if prev_gravity is not None and prev_gravity != gravity:
        diff = gravity - prev_gravity
        if diff > 0:
            parts.append(f"\nGravity increase ayyindi ante, downward pull strong avutundi. ")
            parts.append(f"Flight time and maximum height both decrease avutundi. ")
            parts.append(f"Example: Moon lo gravity 1.6 m/s², Jupiter lo 24.8 m/s². Moon lo projectile more distance travel avutundi. ")
        else:
            parts.append(f"\nGravity decrease ayyindi ante, downward pull weak avutundi. ")
            parts.append(f"Flight time and maximum height both increase avutundi. ")
    
    return " ".join(parts)


def generate_chunked_explanations(angle: float, velocity: float, gravity: float,
                                   prev_angle: Optional[float] = None, 
                                   prev_velocity: Optional[float] = None, 
                                   prev_gravity: Optional[float] = None,
                                   custom_formula: Optional[str] = None,
                                   include_formula: bool = False) -> List[AudioChunk]:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from physics_service import calculate_trajectory
    
    result = calculate_trajectory(angle, velocity, gravity)
    angle_rad = angle * math.pi / 180
    vx = velocity * math.cos(angle_rad)
    vy = velocity * math.sin(angle_rad)
    
    chunks = []
    
    chunks.append(AudioChunk(
        chunk_id="intro",
        title="Introduction to Projectile Motion",
        title_te="ప్రొజెక్టైల్ మోషన్ పరిచయం",
        text=f"Let's learn about projectile motion! When we launch an object at an angle, it follows a curved path called a trajectory. In this simulation, we launch a projectile at {angle} degrees with an initial velocity of {velocity} meters per second.",
        text_te=f"Projectile motion theory ante, niiku explain cheyyali! Eppudaina object ni angle lo launch cheyyamante, adhi curved path lo travel avutundi. I simulation lo, projectile ni {angle} degrees angle lo, {velocity} m/s velocity tho launch cheyyagane.",
        category="concept"
    ))
    
    chunks.append(AudioChunk(
        chunk_id="components",
        title="Velocity Components Explained",
        title_te="వెలాసిటీ కాంపొనెంట్స్ వివరణ",
        text=f"The initial velocity gets split into two parts. The first part, which acts sideways, is {vx:.2f} m/s, and the second part, which acts up and down, is {vy:.2f} m/s. The sideways acting part stays the same throughout because there's no air resistance. The up and down acting part changes due to gravity.",
        text_te=f"Ipudu initial velocity ni two components lo split cheyyali. Sideways component = {vx:.2f} m/s. Vertical component = {vy:.2f} m/s. Sideways motion lo gravity effect ledu kabbati constant velocity tho move avutundi. Vertical motion lo gravity {gravity} m/s² impact undi.",
        category="concept"
    ))
    
    chunks.append(AudioChunk(
        chunk_id="formulas",
        title="Key Formulas",
        title_te="ముఖ్యమైన ఫార్ములాలు",
        text=f"Remember these important formulas! For the distance traveled: x equals v cos theta times t. For vertical height: y equals v sin theta times t minus half g t squared. These help us calculate the projectile's position at any time.",
        text_te=f"Eppudu formulas remember cheyyandi! Sideways distance ki: x = v cos theta times t. Vertical height ki: y = v sin theta times t minus half g t squared. Ippudu maximum height, range, flight time formulas check cheyyamandi.",
        category="formula"
    ))
    
    chunks.append(AudioChunk(
        chunk_id="results",
        title="Simulation Results",
        title_te="సిమ్యులేషన్ ఫలితాలు",
        text=f"Here are your simulation results! Maximum height reached: {result['max_height']:.2f} meters. Total distance covered: {result['range']:.2f} meters. Time of flight: {result['time_of_flight']:.2f} seconds. These results depend on your angle and velocity settings.",
        text_te=f"Ipudu results choodamandi! Maximum height = {result['max_height']:.2f} meters. Total range = {result['range']:.2f} meters. Time of flight = {result['time_of_flight']:.2f} seconds. Kabbati 45° angle maximum range ki ideal.",
        category="results"
    ))
    
    if prev_angle is not None and prev_angle != angle:
        diff = angle - prev_angle
        direction_en = "increased" if diff > 0 else "decreased"
        direction_te = "increase ayyindi" if diff > 0 else "decrease ayyindi"
        if diff > 0:
            chunks.append(AudioChunk(
                chunk_id="angle_change_up",
                title="Angle Increased Effect",
                title_te="ఏంగిల్ పెరిగినప్పుడు",
                text=f"You increased the angle from {prev_angle} to {angle} degrees. Higher angle means the projectile goes higher but travels a shorter distance. The up and down part increases while the sideways part decreases.",
                text_te=f"Angle {prev_angle} నుండి {angle} degrees కి {direction_te}. Higher angle ante, projectile more height ki reach avutundi but short distance travel avutundi. Vertical component increase avutundi. Sideways component decrease avutundi.",
                category="change"
            ))
        else:
            chunks.append(AudioChunk(
                chunk_id="angle_change_down",
                title="Angle Decreased Effect",
                title_te="ఏంగిల్ తగ్గినప్పుడు",
                text=f"You decreased the angle from {prev_angle} to {angle} degrees. Lower angle means the projectile travels farther but reaches a lower maximum height. The sideways part increases while the up and down part decreases.",
                text_te=f"Angle {prev_angle} నుండి {angle} degrees కి {direction_te}. Lower angle ante, projectile more distance travel avutundi but low height ki reach avutundi. Sideways component increase avutundi. Vertical component decrease avutundi.",
                category="change"
            ))
    
    if prev_velocity is not None and prev_velocity != velocity:
        diff = velocity - prev_velocity
        direction_en = "increased" if diff > 0 else "decreased"
        direction_te = "increase ayyindi" if diff > 0 else "decrease ayyindi"
        if diff > 0:
            chunks.append(AudioChunk(
                chunk_id="velocity_change_up",
                title="Velocity Increased Effect",
                title_te="వెలాసిటీ పెరిగినప్పుడు",
                text=f"You increased the velocity from {prev_velocity} to {velocity} meters per second. Higher velocity means the projectile has more initial energy, so both height and range increase. Remember: range and height are proportional to velocity squared!",
                text_te=f"Velocity {prev_velocity} నుండి {velocity} m/s కి {direction_te}. Higher velocity ante, projectile more initial energy undi. Kabbati both height and range increase avutundi. Physics lo, Range ∝ v² and Height ∝ v².",
                category="change"
            ))
        else:
            chunks.append(AudioChunk(
                chunk_id="velocity_change_down",
                title="Velocity Decreased Effect",
                title_te="వెలాసిటీ తగ్గినప్పుడు",
                text=f"You decreased the velocity from {prev_velocity} to {velocity} meters per second. Lower velocity means less initial energy, so both height and range decrease.",
                text_te=f"Velocity {prev_velocity} నుండి {velocity} m/s కి {direction_te}. Lower velocity ante, initial energy decrease avutundi. Kabbati both height and range decrease avutundi.",
                category="change"
            ))
    
    if prev_gravity is not None and prev_gravity != gravity:
        diff = gravity - prev_gravity
        direction_te = "increase ayyindi" if diff > 0 else "decrease ayyindi"
        if diff > 0:
            chunks.append(AudioChunk(
                chunk_id="gravity_change_up",
                title="Gravity Increased Effect",
                title_te="గ్రావిటీ పెరిగినప్పుడు",
                text=f"You increased gravity from {prev_gravity} to {gravity} meters per second squared. Stronger gravity pulls the projectile down faster, reducing both flight time and maximum height. Compare: Moon has 1.6 m/s², Earth has 9.81 m/s², Jupiter has 24.8 m/s²!",
                text_te=f"Gravity {prev_gravity} నుండి {gravity} m/s² కి {direction_te}. Stronger gravity ante, projectile fast ga ground ki vellipovali. Kabbati flight time and maximum height both decrease avutundi. Moon lo gravity 1.6, Jupiter lo 24.8.",
                category="change"
            ))
        else:
            chunks.append(AudioChunk(
                chunk_id="gravity_change_down",
                title="Gravity Decreased Effect",
                title_te="గ్రావిటీ తగ్గినప్పుడు",
                text=f"You decreased gravity from {prev_gravity} to {gravity} meters per second squared. Weaker gravity means the projectile stays in the air longer and reaches a higher maximum height.",
                text_te=f"Gravity {prev_gravity} నుండి {gravity} m/s² కి {direction_te}. Weak gravity ante, projectile long time air lo undi and more height reach avutundi.",
                category="change"
            ))
    
    chunks.append(AudioChunk(
        chunk_id="summary",
        title="Key Takeaways",
        title_te="ముఖ్యమైన అంశాలు",
        text=f"Let me summarize the key points! The angle determines how high and far the projectile goes. The velocity affects both height and range. Gravity pulls the projectile down. For maximum range on Earth, an angle of 45 degrees is ideal. Try different combinations to see how these parameters interact!",
        text_te=f"Ipudu key points summarize cheyyamandi! Angle ante, projectile height and distance decide avutundi. Velocity ante, both height and range affect avutundi. Gravity ante, projectile ni ground ki pull cheyyutundi. Earth lo maximum range ki 45° ideal angle. Experimentation cheyyandi!",
        category="summary"
    ))
    
    if include_formula and custom_formula:
        formula_speech = _convert_formula_to_speech(custom_formula)
        chunks.append(AudioChunk(
            chunk_id="custom_formula",
            title="Custom Formula Explanation",
            title_te="కస్టమ్ ఫార్ములా వివరణ",
            text=f"You're using a custom formula: {formula_speech}. This formula describes the relationship between the sideways distance, vertical height, launch angle, initial velocity, and gravity. In this formula, y represents vertical height, x represents sideways distance, theta represents launch angle, v represents velocity, and g represents gravity.",
            text_te=f"Niiku custom formula use cheyyataaniki: {formula_speech}. I formula lo y = vertical height, x = sideways distance, theta = launch angle, v = velocity, g = gravity.",
            category="formula"
        ))
    
    return chunks


def synthesize_chunk(chunk: AudioChunk, language: str = "en-IN") -> AudioChunk:
    if language == "te-IN":
        text = chunk.text_te
    else:
        text = chunk.text
    
    result = synthesize_speech(text, target_language_code=language)
    
    if result.get("audio_url"):
        if language == "te-IN":
            chunk.audio_url_te = result["audio_url"]
        else:
            chunk.audio_url_en = result["audio_url"]
    
    return chunk


def generate_speech_explanation(angle: float, velocity: float, gravity: float,
                                prev_angle: Optional[float] = None, prev_velocity: Optional[float] = None,
                                prev_gravity: Optional[float] = None,
                                custom_formula: Optional[str] = None,
                                include_formula: bool = False,
                                language: str = "en-IN") -> dict:
    if language == "te-IN":
        explanation_text = generate_explanation_text_telugu(
            angle, velocity, gravity,
            prev_angle, prev_velocity, prev_gravity,
            custom_formula, include_formula
        )
    else:
        explanation_text = generate_explanation_text(
            angle, velocity, gravity,
            prev_angle, prev_velocity, prev_gravity,
            custom_formula, include_formula
        )
    
    return synthesize_speech(explanation_text, target_language_code=language)


def combine_audio_chunks(audio_urls: List[str]) -> Optional[str]:
    if not PYDUB_AVAILABLE or AudioSegment is None:
        print("pydub not installed. Cannot combine audio chunks.")
        return None
    
    if not audio_urls:
        return None
    
    try:
        import wave
        
        combined_seg = AudioSegment.empty()
        target_sample_rate = 16000
        target_channels = 1
        valid_chunks = 0
        
        for i, url in enumerate(audio_urls):
            if not url:
                print(f"Warning: Empty URL for chunk {i}")
                continue
            
            if url.startswith("data:audio"):
                base64_data = url.split(",")[1]
                audio_bytes = base64.b64decode(base64_data)
                
                try:
                    wav_reader = wave.open(io.BytesIO(audio_bytes), 'rb')
                    wav_reader.close()
                    
                    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                    
                    if audio.frame_rate != target_sample_rate:
                        audio = audio.set_frame_rate(target_sample_rate)
                    if audio.channels != target_channels:
                        audio = audio.set_channels(target_channels)
                    
                    combined_seg += audio
                    
                    if i < len(audio_urls) - 1:
                        silence_duration_ms = 500
                        silence = AudioSegment.silent(duration=silence_duration_ms, frame_rate=target_sample_rate)
                        combined_seg += silence
                    valid_chunks += 1
                except wave.Error as e:
                    print(f"Warning: Could not parse WAV for chunk {i}: {e}. Retrying with different approach...")
                    try:
                        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
                        if audio.frame_rate != target_sample_rate:
                            audio = audio.set_frame_rate(target_sample_rate)
                        if audio.channels != target_channels:
                            audio = audio.set_channels(target_channels)
                        combined_seg += audio
                        if i < len(audio_urls) - 1:
                            silence_duration_ms = 500
                            silence = AudioSegment.silent(duration=silence_duration_ms, frame_rate=target_sample_rate)
                            combined_seg += silence
                        valid_chunks += 1
                        print(f"Chunk {i} recovered successfully")
                    except Exception as retry_error:
                        print(f"Failed to recover chunk {i}: {retry_error}")
                        continue
                except Exception as e:
                    print(f"Error processing chunk {i}: {e}")
                    continue
        
        if valid_chunks == 0:
            print("No valid audio chunks to combine")
            return None
        
        if len(combined_seg) == 0:
            print("Combined audio is empty")
            return None
        
        output_buffer = io.BytesIO()
        combined_seg.set_frame_rate(target_sample_rate)
        combined_seg.export(output_buffer, format="wav")
        output_buffer.seek(0)
        
        audio_base64 = base64.b64encode(output_buffer.read()).decode("utf-8")
        return f"data:audio/wav;base64,{audio_base64}"
    except Exception as e:
        print(f"Error combining audio chunks: {e}")
        import traceback
        traceback.print_exc()
        return None