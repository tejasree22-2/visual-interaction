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

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    logger.warning("ffmpeg: NOT FOUND")
    return False

FFMPEG_AVAILABLE = _check_ffmpeg()


class AudioChunk:
    def __init__(self, chunk_id: str, title: str, text: str, category: str = "general"):
        self.chunk_id = chunk_id
        self.title = title
        self.text = text
        self.category = category
        self.audio_url_en = None
    
    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "title": self.title,
            "text": self.text,
            "category": self.category,
            "audio_url_en": self.audio_url_en
        }


def _convert_formula_to_speech(formula: str) -> str:
    if not formula:
        return formula
    return (formula
            .replace('θ', 'theta')
            .replace('²', ' squared')
            .replace('³', ' cubed')
            .replace('*', ' multiplied by ')
            .replace('/', ' per ')
            .replace('+', ' plus ')
            .replace('-', ' minus ')
            .replace('=', ' equals ')
            .replace('(', ' open parenthesis ')
            .replace(')', ' close parenthesis ')
            .replace('×', ' times ')
            .replace('½', ' half '))


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
        logger.error("SARVAM_API_KEY not found in environment variables")
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
                      max_chars: int = 2000) -> dict:
    api_key = get_api_key()
    
    if not api_key:
        logger.error("TTS: API key missing")
        return {"error": "API key missing", "audio_url": None, "error_code": "MISSING_API_KEY"}
    
    if not PYDUB_AVAILABLE:
        logger.warning("pydub not installed")
    
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
    
    logger.info(f"TTS: lang={target_language_code}, text_length={len(clean_text)}")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"TTS API call (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("audios") and len(result["audios"]) > 0:
                audio_base64 = result["audios"][0]
                if not audio_base64 or len(audio_base64) < 500:
                    logger.warning(f"TTS: Suspiciously short audio data ({len(audio_base64) if audio_base64 else 0} chars)")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                        continue
                    logger.error("TTS: Audio data too short")
                    return {"error": "Audio data too short", "audio_url": None, "error_code": "SHORT_AUDIO"}
                
                logger.info(f"TTS: Received audio data ({len(audio_base64)} chars base64)")
                
                if save_file:
                    import hashlib
                    import os
                    audio_hash = hashlib.md5((text + target_language_code).encode()).hexdigest()[:16]
                    media_dir = os.path.join(project_root, "media")
                    os.makedirs(media_dir, exist_ok=True)
                    audio_path = os.path.join(media_dir, f"speech_{audio_hash}.mp3")
                    
                    audio_bytes = base64.b64decode(audio_base64)
                    try:
                        if PYDUB_AVAILABLE and AudioSegment:
                            audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                            audio.export(audio_path, format="mp3", bitrate="64k")
                            logger.info(f"TTS: Saved to {audio_path}")
                            return {
                                "audio_url": f"/media/speech_{audio_hash}.mp3",
                                "request_id": result.get("request_id")
                            }
                        else:
                            logger.error("TTS: pydub not installed")
                            return {"error": "pydub not installed", "audio_url": None, "error_code": "PYDUB_MISSING"}
                    except Exception as e:
                        logger.error(f"TTS: Could not convert to MP3 - {e}")
                        if not FFMPEG_AVAILABLE:
                            logger.error("TTS: ffmpeg is required for audio conversion")
                        return {"error": f"Could not convert audio: {str(e)}", "audio_url": None, "error_code": "CONVERSION_FAILED"}
                
                audio_data_url = f"data:audio/wav;base64,{audio_base64}"
                return {
                    "audio_url": audio_data_url,
                    "request_id": result.get("request_id")
                }
            else:
                logger.warning(f"TTS: No audio returned (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                    continue
                logger.error("TTS: API returned no audio data")
                return {"error": "No audio returned from API", "audio_url": None, "error_code": "NO_AUDIO_RESPONSE"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS: API request failed (attempt {attempt + 1}/{max_retries}) - {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
                continue
            return {"error": f"API request failed: {str(e)}", "audio_url": None, "error_code": "REQUEST_FAILED"}
        except Exception as e:
            logger.error(f"TTS: Unexpected error - {e}")
            return {"error": str(e), "audio_url": None, "error_code": "UNEXPECTED_ERROR"}
    
    logger.error("TTS: Max retries exceeded")
    return {"error": "Max retries exceeded", "audio_url": None, "error_code": "MAX_RETRIES"}


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
        text=f"Let's learn about projectile motion! When we launch an object at {angle} degrees with velocity {velocity} meters per second, it follows a curved path called trajectory. The initial velocity splits into two components: horizontal component {vx:.2f} m/s and vertical component {vy:.2f} m/s. The key formulas are: x equals v cos theta times t for horizontal distance, and y equals v sin theta times t minus half g t squared for vertical height. Your simulation results: maximum height {result['max_height']:.2f} meters, total range {result['range']:.2f} meters, and time of flight {result['time_of_flight']:.2f} seconds. Remember: 45 degrees gives maximum range on Earth!",
        category="main"
    ))
    
    return chunks


def synthesize_chunk(chunk: AudioChunk, language: str = "en-IN", save_to_file: bool = True) -> AudioChunk:
    text = chunk.text
    
    if save_to_file:
        result = synthesize_speech(text, target_language_code=language, save_file=True)
    else:
        result = synthesize_speech(text, target_language_code=language)
    
    if result.get("audio_url"):
        chunk.audio_url_en = result["audio_url"]
    
    return chunk


def combine_audio_chunks(audio_urls: List[str], output_format: str = "mp3") -> Optional[str]:
    if not PYDUB_AVAILABLE or AudioSegment is None:
        logger.error("Combine: pydub not installed")
        return None
    
    if not FFMPEG_AVAILABLE:
        logger.warning("ffmpeg not found")
    
    if not audio_urls:
        logger.warning("Combine: No audio URLs provided")
        return None
    
    logger.info(f"Combine: Starting to combine {len(audio_urls)} audio chunks")
    
    try:
        import wave
        import hashlib
        import os
        
        combined_seg = AudioSegment.empty()
        target_sample_rate = 16000
        target_channels = 1
        valid_chunks = 0
        failed_chunks = 0
        
        media_dir = os.path.join(project_root, "media")
        
        for i, url in enumerate(audio_urls):
            if not url:
                logger.warning(f"Combine: Skipping empty URL at index {i}")
                failed_chunks += 1
                continue
            
            audio = None
            audio_bytes = None
            
            if url.startswith("/media/"):
                file_path = os.path.join(media_dir, os.path.basename(url))
                if os.path.exists(file_path):
                    try:
                        logger.info(f"Combine: Loading file {file_path}")
                        audio = AudioSegment.from_file(file_path)
                    except Exception as e:
                        logger.error(f"Combine: Could not load file {file_path} - {e}")
                        failed_chunks += 1
                        continue
                else:
                    logger.error(f"Combine: File not found - {file_path}")
                    failed_chunks += 1
                    continue
            elif url.startswith("data:audio"):
                try:
                    base64_data = url.split(",", 1)[1]
                    audio_bytes = base64.b64decode(base64_data)
                    logger.info(f"Combine: Decoded base64 audio ({len(audio_bytes)} bytes)")
                except Exception as e:
                    logger.error(f"Combine: Could not decode base64 audio - {e}")
                    failed_chunks += 1
                    continue
            
            if audio_bytes:
                try:
                    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                except Exception:
                    try:
                        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
                    except Exception as e:
                        logger.error(f"Combine: Could not parse audio bytes - {e}")
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
                    logger.info(f"Combine: Chunk {i+1} added successfully")
                except Exception as e:
                    logger.error(f"Combine: Error processing chunk {i+1} - {e}")
                    failed_chunks += 1
                    continue
        
        logger.info(f"Combine: Processed {valid_chunks} chunks successfully, {failed_chunks} failed")
        
        if valid_chunks == 0:
            logger.error("Combine: No valid audio chunks to combine")
            return None
        
        if len(combined_seg) == 0:
            logger.error("Combine: Combined audio is empty")
            return None
        
        combined_seg = combined_seg.set_frame_rate(target_sample_rate)
        combined_seg = combined_seg.set_channels(target_channels)
        
        audio_hash = hashlib.md5(str(audio_urls).encode()).hexdigest()[:16]
        os.makedirs(media_dir, exist_ok=True)
        
        if output_format == "mp3":
            output_path = os.path.join(media_dir, f"combined_{audio_hash}.mp3")
            try:
                combined_seg.export(output_path, format="mp3", bitrate="64k")
                logger.info(f"Combine: Exported to {output_path}")
                return f"/media/combined_{audio_hash}.mp3"
            except Exception as e:
                logger.error(f"Combine: Could not export MP3 - {e}")
                if not FFMPEG_AVAILABLE:
                    logger.error("Combine: ffmpeg is required for MP3 export")
                return None
        else:
            output_path = os.path.join(media_dir, f"combined_{audio_hash}.wav")
            combined_seg.export(output_path, format="wav")
            logger.info(f"Combine: Exported to {output_path}")
            return f"/media/combined_{audio_hash}.wav"
    except Exception as e:
        logger.error(f"Combine: Unexpected error - {e}")
        return None