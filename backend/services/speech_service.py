import os
import base64
import requests
import io
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv
import math
import logging
import subprocess

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False

logger = logging.getLogger('visual-interaction-backend.speech')

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

SARVAM_API_URL = "https://api.sarvam.ai/text-to-speech"


def _check_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("ffmpeg: FOUND")
            return True
    except Exception:
        pass
    logger.warning("ffmpeg: NOT FOUND - Audio conversion may fail")
    return False

FFMPEG_AVAILABLE = _check_ffmpeg()


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


def _number_to_words(num: float) -> str:
    if num == int(num):
        num_int = int(num)
        if num_int < 0:
            return "minus " + _int_to_words(-num_int)
        return _int_to_words(num_int)
    
    parts = str(num).split('.')
    integer_part = int(parts[0])
    decimal_part = parts[1]
    
    result = _number_to_words(float(integer_part)) if integer_part != 0 else "zero"
    result += " point " + " ".join(_digit_to_word(d) for d in decimal_part)
    return result


def _int_to_words(n: int) -> str:
    if n < 0:
        return "minus " + _int_to_words(-n)
    if n == 0:
        return "zero"
    
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    if n < 20:
        return ones[n]
    elif n < 100:
        return tens[n // 10] + ("-" + ones[n % 10] if n % 10 != 0 else "")
    elif n < 1000:
        return ones[n // 100] + " hundred" + (" " + _int_to_words(n % 100) if n % 100 != 0 else "")
    elif n < 1000000:
        return _int_to_words(n // 1000) + " thousand" + (" " + _int_to_words(n % 1000) if n % 1000 != 0 else "")
    elif n < 1000000000:
        return _int_to_words(n // 1000000) + " million" + (" " + _int_to_words(n % 1000000) if n % 1000000 != 0 else "")
    else:
        return _int_to_words(n // 1000000000) + " billion" + (" " + _int_to_words(n % 1000000000) if n % 1000000000 != 0 else "")


def _digit_to_word(d: str) -> str:
    return ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][int(d)]


def get_api_key():
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        logger.error("SARVAM_API_KEY not found in environment variables!")
        logger.error("Please add SARVAM_API_KEY to your .env file")
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
    
    parts.append(f"In this projectile motion simulation, the projectile is launched at an angle of {_number_to_words(angle)} degrees with an initial velocity of {_number_to_words(velocity)} meters per second under a gravitational acceleration of {_number_to_words(gravity)} meters per second squared.")
    
    if prev_angle is not None and prev_angle != angle:
        change = angle - prev_angle
        direction = "increased" if change > 0 else "decreased"
        parts.append(f"The launch angle has {direction} from {_number_to_words(prev_angle)} to {_number_to_words(angle)} degrees. ")
        if angle > prev_angle:
            parts.append(f"A higher angle means the projectile reaches a greater maximum height but travels a shorter distance. ")
        else:
            parts.append(f"A lower angle means the projectile travels farther but reaches a lower maximum height. ")
    
    if prev_velocity is not None and prev_velocity != velocity:
        change = velocity - prev_velocity
        direction = "increased" if change > 0 else "decreased"
        parts.append(f"The initial velocity has {direction} from {_number_to_words(prev_velocity)} to {_number_to_words(velocity)} meters per second. ")
        if velocity > prev_velocity:
            parts.append(f"Higher velocity means the projectile travels faster and reaches further. ")
        else:
            parts.append(f"Lower velocity means the projectile travels slower and doesn't go as far. ")
    
    if prev_gravity is not None and prev_gravity != gravity:
        change = gravity - prev_gravity
        direction = "increased" if change > 0 else "decreased"
        parts.append(f"The gravitational acceleration has {direction} from {_number_to_words(prev_gravity)} to {_number_to_words(gravity)} meters per second squared. ")
        if gravity > prev_gravity:
            parts.append(f"Stronger gravity pulls the projectile down faster, reducing both the flight time and the maximum height. ")
        else:
            parts.append(f"Weaker gravity lets the projectile stay in the air longer and reach a higher maximum height. ")
    
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from physics_service import calculate_trajectory
    result = calculate_trajectory(angle, velocity, gravity)
    
    parts.append(f"The maximum height reached is {_number_to_words(result['max_height'])} meters. ")
    parts.append(f"The total range or distance covered is {_number_to_words(result['range'])} meters. ")
    parts.append(f"The projectile remains in the air for {_number_to_words(result['time_of_flight'])} seconds.")
    
    return " ".join(parts)


def synthesize_speech(text: str, target_language_code: str = "en-IN", 
                      speaker: str = "arya", max_retries: int = 3,
                      save_file: bool = False,
                      max_chars: int = 500) -> dict:
    api_key = get_api_key()
    
    if not api_key:
        logger.error("TTS FAILED: API key missing")
        return {"error": "API key missing - check .env file", "audio_url": None, "error_code": "MISSING_API_KEY"}
    
    if not PYDUB_AVAILABLE:
        logger.warning("pydub not installed - audio conversion may fail")
    
    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }
    
    clean_text = text.replace('\n', ' ').strip()
    text_was_truncated = False
    if len(clean_text) > max_chars:
        clean_text = clean_text[:max_chars]
        if clean_text.rfind('.') > max_chars - 50:
            clean_text = clean_text[:clean_text.rfind('.') + 1]
        text_was_truncated = True
        logger.warning(f"Text truncated from {len(text)} to {len(clean_text)} characters for Sarvam API")
    
    payload = {
        "inputs": [clean_text],
        "target_language_code": target_language_code,
        "speaker": "shruti",
        "model": "bulbul:v3",
        "speech_sample_rate": 16000
    }
    
    logger.info(f"TTS Request: lang={target_language_code}, text_length={len(clean_text)}, truncated={text_was_truncated}, save_file={save_file}")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"TTS API call (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("audios") and len(result["audios"]) > 0:
                audio_base64 = result["audios"][0]
                if not audio_base64 or len(audio_base64) < 500:
                    logger.warning(f"TTS: Suspiciously short audio data ({len(audio_base64) if audio_base64 else 0} chars) for text: {text[:50]}...")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                        continue
                    logger.error("TTS FAILED: Audio data too short")
                    return {"error": "Audio data too short - API returned invalid data", "audio_url": None, "error_code": "SHORT_AUDIO"}
                
                logger.info(f"TTS SUCCESS: Received audio data ({len(audio_base64)} chars base64)")
                
                if save_file:
                    import hashlib
                    import os
                    audio_hash = hashlib.md5((text + target_language_code).encode()).hexdigest()[:16]
                    media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
                    os.makedirs(media_dir, exist_ok=True)
                    audio_path = os.path.join(media_dir, f"speech_{audio_hash}.mp3")
                    
                    audio_bytes = base64.b64decode(audio_base64)
                    try:
                        if PYDUB_AVAILABLE and AudioSegment:
                            audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                            audio.export(audio_path, format="mp3", bitrate="64k")
                            logger.info(f"TTS SAVED: {audio_path}")
                            return {
                                "audio_url": f"/media/speech_{audio_hash}.mp3",
                                "request_id": result.get("request_id")
                            }
                        else:
                            logger.error("TTS FAILED: pydub not installed")
                            return {"error": "pydub not installed - cannot convert audio", "audio_url": None, "error_code": "PYDUB_MISSING"}
                    except Exception as e:
                        logger.error(f"TTS ERROR: Could not convert to MP3: {e}")
                        if not FFMPEG_AVAILABLE:
                            logger.error("TTS ERROR: ffmpeg is required for audio conversion. Please install ffmpeg.")
                        return {"error": f"Could not convert audio: {str(e)}", "audio_url": None, "error_code": "CONVERSION_FAILED"}
                
                audio_data_url = f"data:audio/wav;base64,{audio_base64}"
                return {
                    "audio_url": audio_data_url,
                    "request_id": result.get("request_id")
                }
            else:
                logger.warning(f"TTS: No audio returned from API for text: {text[:50]}... (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                    continue
                logger.error("TTS FAILED: API returned no audio data")
                return {"error": "No audio returned from API", "audio_url": None, "error_code": "NO_AUDIO_RESPONSE"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS ERROR: API request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
                continue
            return {"error": f"API request failed: {str(e)}", "audio_url": None, "error_code": "REQUEST_FAILED"}
        except Exception as e:
            logger.error(f"TTS ERROR: Unexpected error: {e}")
            return {"error": str(e), "audio_url": None, "error_code": "UNEXPECTED_ERROR"}
    
    logger.error("TTS FAILED: Max retries exceeded")
    return {"error": "Max retries exceeded", "audio_url": None, "error_code": "MAX_RETRIES"}


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
    
    parts.append(f"Okay, ante results: ")
    parts.append(f"Maximum height = {result['max_height']:.2f} meters. ")
    parts.append(f"Total range = {result['range']:.2f} meters. ")
    parts.append(f"Time of flight = {result['time_of_flight']:.2f} seconds. ")
    
    if prev_angle is not None and prev_angle != angle:
        diff = angle - prev_angle
        if diff > 0:
            parts.append(f"So, angle increase ayyindi ante, vertical component increase avutundi. Sideways component decrease avutundi. ")
            parts.append(f"Kabbati maximum height increase avutundi. Range decrease avutundi. ")
            parts.append(f"Remember: 45° max range ki ideal angle. ")
        else:
            parts.append(f"So, angle decrease ayyindi ante, sideways component increase avutundi. Vertical component decrease avutundi. ")
            parts.append(f"Kabbati range increase avutundi. Maximum height decrease avutundi. ")
    
    if prev_velocity is not None and prev_velocity != velocity:
        diff = velocity - prev_velocity
        if diff > 0:
            parts.append(f"Velocity increase ayyindi ante, initial energy increase avutundi. ")
            parts.append(f"Both height and range increase avutundi. Physics ante, Range ∝ v² and Height ∝ v². ")
        else:
            parts.append(f"Velocity decrease ayyindi ante, initial energy decrease avutundi. ")
            parts.append(f"Both height and range decrease avutundi. ")
    
    if prev_gravity is not None and prev_gravity != gravity:
        diff = gravity - prev_gravity
        if diff > 0:
            parts.append(f"Gravity increase ayyindi ante, downward pull strong avutundi. ")
            parts.append(f"Flight time and maximum height both decrease avutundi. ")
            parts.append(f"Example: Moon lo gravity 1.6 m/s², Jupiter lo 24.8 m/s². Moon lo projectile more distance travel avutundi. ")
        else:
            parts.append(f"Gravity decrease ayyindi ante, downward pull weak avutundi. ")
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
        chunk_id="main",
        title="Projectile Motion Basics",
        title_te="ప్రొజెక్టైల్ మోషన్ ప్రాథమికాలు",
        text=f"Let's learn about projectile motion! When we launch an object at {angle} degrees with velocity {velocity} meters per second, it follows a curved path called trajectory. The initial velocity splits into two components: horizontal component {vx:.2f} m/s and vertical component {vy:.2f} m/s. The key formulas are: x equals v cos theta times t for horizontal distance, and y equals v sin theta times t minus half g t squared for vertical height. Your simulation results: maximum height {result['max_height']:.2f} meters, total range {result['range']:.2f} meters, and time of flight {result['time_of_flight']:.2f} seconds. Remember: 45 degrees gives maximum range on Earth!",
        text_te=f"Niiku projectile motion explanation ivvutu! Eppudu projectile ni {angle} degrees angle lo, {velocity} m/s velocity tho launch cheyyagane. Initial velocity ni two components lo split cheyyali. Sideways component = {vx:.2f} m/s, vertical component = {vy:.2f} m/s. Key formulas: horizontal distance ki x = v cos theta times t, vertical height ki y = v sin theta times t minus half g t squared. Results: maximum height = {result['max_height']:.2f} meters, total range = {result['range']:.2f} meters, time of flight = {result['time_of_flight']:.2f} seconds. Earth lo maximum range ki 45 degrees ideal angle!",
        category="main"
    ))
    
    return chunks


def synthesize_chunk(chunk: AudioChunk, language: str = "en-IN", save_to_file: bool = True) -> AudioChunk:
    if language == "te-IN":
        text = chunk.text_te
    else:
        text = chunk.text
    
    if save_to_file:
        result = synthesize_speech(text, target_language_code=language, save_file=True)
    else:
        result = synthesize_speech(text, target_language_code=language)
    
    if result.get("audio_url"):
        if language == "te-IN":
            chunk.audio_url_te = result["audio_url"]
        else:
            chunk.audio_url_en = result["audio_url"]
    
    return chunk


def combine_audio_chunks(audio_urls: List[str], output_format: str = "mp3") -> Optional[str]:
    if not PYDUB_AVAILABLE or AudioSegment is None:
        logger.error("COMBINE FAILED: pydub not installed")
        return None
    
    if not FFMPEG_AVAILABLE:
        logger.warning("ffmpeg not found - audio conversion may fail")
    
    if not audio_urls:
        logger.warning("COMBINE: No audio URLs provided")
        return None
    
    logger.info(f"COMBINE: Starting to combine {len(audio_urls)} audio chunks")
    
    try:
        import wave
        import hashlib
        import os
        
        combined_seg = AudioSegment.empty()
        target_sample_rate = 16000
        target_channels = 1
        valid_chunks = 0
        failed_chunks = 0
        
        media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
        
        for i, url in enumerate(audio_urls):
            if not url:
                logger.warning(f"COMBINE: Skipping empty URL at index {i}")
                failed_chunks += 1
                continue
            
            audio = None
            audio_bytes = None
            
            if url.startswith("/media/"):
                file_path = os.path.join(media_dir, os.path.basename(url))
                if os.path.exists(file_path):
                    try:
                        logger.info(f"COMBINE: Loading file {file_path}")
                        audio = AudioSegment.from_file(file_path)
                    except Exception as e:
                        logger.error(f"COMBINE: Could not load file {file_path}: {e}")
                        failed_chunks += 1
                        continue
                else:
                    logger.error(f"COMBINE: File not found: {file_path}")
                    failed_chunks += 1
                    continue
            elif url.startswith("data:audio"):
                try:
                    base64_data = url.split(",", 1)[1]
                    audio_bytes = base64.b64decode(base64_data)
                    logger.info(f"COMBINE: Decoded base64 audio ({len(audio_bytes)} bytes)")
                except Exception as e:
                    logger.error(f"COMBINE: Could not decode base64 audio: {e}")
                    failed_chunks += 1
                    continue
            
            if audio_bytes:
                try:
                    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                except Exception:
                    try:
                        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
                    except Exception as e:
                        logger.error(f"COMBINE: Could not parse audio bytes: {e}")
                        failed_chunks += 1
                        continue
            
            if audio:
                try:
                    if audio.frame_rate != target_sample_rate:
                        audio = audio.set_frame_rate(target_sample_rate)
                    if audio.channels != target_channels:
                        audio = audio.set_channels(target_channels)
                    
                    if valid_chunks > 0 and len(combined_seg) > 0:
                        combined_seg = combined_seg.append(audio, crossfade=150)
                    else:
                        combined_seg += audio
                    
                    if i < len(audio_urls) - 1:
                        silence = AudioSegment.silent(duration=300, frame_rate=target_sample_rate)
                        combined_seg += silence
                    
                    valid_chunks += 1
                    logger.info(f"COMBINE: Chunk {i+1} added successfully")
                except Exception as e:
                    logger.error(f"COMBINE: Error processing chunk {i+1}: {e}")
                    failed_chunks += 1
                    continue
        
        logger.info(f"COMBINE: Processed {valid_chunks} chunks successfully, {failed_chunks} failed")
        
        if valid_chunks == 0:
            logger.error("COMBINE FAILED: No valid audio chunks to combine")
            return None
        
        if len(combined_seg) == 0:
            logger.error("COMBINE FAILED: Combined audio is empty")
            return None
        
        combined_seg = combined_seg.set_frame_rate(target_sample_rate)
        combined_seg = combined_seg.set_channels(target_channels)
        
        audio_hash = hashlib.md5(str(audio_urls).encode()).hexdigest()[:16]
        os.makedirs(media_dir, exist_ok=True)
        
        if output_format == "mp3":
            output_path = os.path.join(media_dir, f"combined_{audio_hash}.mp3")
            try:
                combined_seg.export(output_path, format="mp3", bitrate="64k")
                logger.info(f"COMBINE SUCCESS: Exported to {output_path}")
                return f"/media/combined_{audio_hash}.mp3"
            except Exception as e:
                logger.error(f"COMBINE FAILED: Could not export MP3: {e}")
                if not FFMPEG_AVAILABLE:
                    logger.error("COMBINE: ffmpeg is required for MP3 export")
                return None
        else:
            output_path = os.path.join(media_dir, f"combined_{audio_hash}.wav")
            combined_seg.export(output_path, format="wav")
            logger.info(f"COMBINE SUCCESS: Exported to {output_path}")
            return f"/media/combined_{audio_hash}.wav"
    except Exception as e:
        logger.error(f"COMBINE FAILED: Unexpected error: {e}")
        import traceback
        logger.error(f"COMBINE: Traceback: {traceback.format_exc()}")
        return None