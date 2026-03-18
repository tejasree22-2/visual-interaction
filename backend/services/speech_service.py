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
    
    parts.append(f"Hello everyone! Niiku projectile motion ni explanation ivvutu. ")
    parts.append(f"Ipudu i simulation lo, projectile {angle} degrees angle daari, {velocity} m/s velocity tho launch avutundi. ")
    parts.append(f"Ekkada velocity ni two components lo split cheyyali. Horizontal component = {velocity * math.cos(angle_rad):.2f} m/s. Vertical component = {velocity * math.sin(angle_rad):.2f} m/s. ")
    parts.append(f"Horizontal motion lo, gravity effect ledu. Kabbati constant velocity tho move avutundi. Formula: x = v cosθ × t. ")
    parts.append(f"Vertical motion lo, gravity {gravity} m/s² impact undi. Upward movement lo velocity decrease avutundi, downward movement lo increase avutundi. Formula: y = v sinθ × t - ½gt². ")
    
    parts.append(f"\nOkay, ante results: ")
    parts.append(f"Maximum height = {result['max_height']:.2f} meters. ")
    parts.append(f"Total range = {result['range']:.2f} meters. ")
    parts.append(f"Time of flight = {result['time_of_flight']:.2f} seconds. ")
    
    if prev_angle is not None and prev_angle != angle:
        diff = angle - prev_angle
        if diff > 0:
            parts.append(f"\nSo, angle increase ayyindi ante, vertical component increase avutundi. Horizontal component decrease avutundi. ")
            parts.append(f"Kabbati maximum height increase avutundi. Range decrease avutundi. ")
            parts.append(f"Remember: 45° max range ki ideal angle. ")
        else:
            parts.append(f"\nSo, angle decrease ayyindi ante, horizontal component increase avutundi. Vertical component decrease avutundi. ")
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