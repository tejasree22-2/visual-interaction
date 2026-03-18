import os
import base64
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import math

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

SARVAM_API_URL = "https://api.sarvam.ai/text-to-speech"


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
        parts.append("This formula describes the relationship between the horizontal distance, vertical height, launch angle, initial velocity, and gravity. ")
        parts.append("In this formula, y represents the vertical height, x represents the horizontal distance, theta represents the launch angle, v represents the initial velocity, and g represents gravitational acceleration. ")
    
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
    parts.append(f"The total range or horizontal distance covered is {result['range']} meters. ")
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
        "speaker": speaker,
        "model": "bulbul:v2",
        "speech_sample_rate": 16000
    }
    
    try:
        response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("audios") and len(result["audios"]) > 0:
            audio_base64 = result["audios"][0]
            audio_data_url = f"data:audio/wav;base64,{audio_base64}"
            return {
                "audio_url": audio_data_url,
                "request_id": result.get("request_id")
            }
        else:
            return {"error": "No audio returned from API", "audio_url": None}
            
    except requests.exceptions.RequestException as e:
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
    
    parts.append(f"Projectile Motion Theory: ")
    parts.append(f"Projectile motion లో object horizontal direction లao constant velocity {velocity * math.cos(angle_rad):.2f} m/sతో move avutundi. ")
    parts.append(f"Vertical direction లao gravity {gravity} m/s² cause vertical velocity change avutundi. ")
    parts.append(f"Horizontal motion: x = v cosθ t. Vertical motion: y = v sinθ t - ½gt². ")
    
    parts.append(f"\nResults: ")
    parts.append(f"Launch angle = {angle}°, initial velocity = {velocity} m/s, gravity = {gravity} m/s². ")
    parts.append(f"Maximum height = {result['max_height']:.2f} m. ")
    parts.append(f"Total range = {result['range']:.2f} m. ")
    parts.append(f"Time of flight = {result['time_of_flight']:.2f} seconds. ")
    
    if prev_angle is not None and prev_angle != angle:
        diff = angle - prev_angle
        if diff > 0:
            parts.append(f"\nAngle change: {prev_angle}° → {angle}° (increase). ")
            parts.append(f"Theory: Higher angle = more vertical component, less horizontal component. ")
            parts.append(f"Result: Height increase, range decrease. ")
            parts.append(f"45° maximum range achieve avutundi. ")
        else:
            parts.append(f"\nAngle change: {prev_angle}° → {angle}° (decrease). ")
            parts.append(f"Theory: Lower angle = more horizontal component. ")
            parts.append(f"Result: Range increase, height decrease. ")
    
    if prev_velocity is not None and prev_velocity != velocity:
        diff = velocity - prev_velocity
        if diff > 0:
            parts.append(f"\nVelocity change: {prev_velocity} → {velocity} m/s (increase). ")
            parts.append(f"Theory: More initial velocity = more kinetic energy. ")
            parts.append(f"Height and range both increase. ")
            parts.append(f"Formula: Range ∝ v², Height ∝ v². ")
        else:
            parts.append(f"\nVelocity change: {prev_velocity} → {velocity} m/s (decrease). ")
            parts.append(f"Theory: Less initial velocity = less energy. ")
            parts.append(f"Height and range both decrease. ")
    
    if prev_gravity is not None and prev_gravity != gravity:
        diff = gravity - prev_gravity
        if diff > 0:
            parts.append(f"\nGravity change: {prev_gravity} → {gravity} m/s² (increase). ")
            parts.append(f"Theory: Stronger gravity pulls down faster. ")
            parts.append(f"Flight time and height both decrease. ")
            parts.append(f"Example: Moon (1.6) less distance, Jupiter (24.8) less distance. ")
        else:
            parts.append(f"\nGravity change: {prev_gravity} → {gravity} m/s² (decrease). ")
            parts.append(f"Theory: Weaker gravity = less downward pull. ")
            parts.append(f"Flight time and height both increase. ")
    
    return " ".join(parts)


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