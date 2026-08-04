import os
import json
import urllib.request
import urllib.error

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")

def generate_nutrition_fallback_response(query_text, user_context=None):
    """
    Intelligent fallback response engine providing structured dietary insights 
    when external API keys are omitted or rate-limited.
    """
    user_context = user_context or {}
    query_lower = (query_text or "").lower()
    goal = str(user_context.get("goal", "healthy maintenance")).lower()
    
    if "protein" in query_lower:
        return ("To boost your protein intake: Include lean options such as Greek yogurt, egg whites, "
                "cottage cheese, lentils, tofu, and grilled chicken. Aim for 1.2g - 2.0g of protein per kg of body weight.")
    elif "water" in query_lower or "hydrat" in query_lower:
        return ("Hydration is essential for metabolic efficiency! Aim for 2.5 to 3.5 liters of water daily. "
                "Drinking a glass of water 20 minutes before meals helps regulate appetite.")
    elif "weight loss" in query_lower or "lose weight" in query_lower or "fat" in query_lower:
        return ("For sustainable weight loss: Maintain a moderate caloric deficit (300-500 kcal below TDEE), "
                "prioritize high-fiber vegetables, lean protein to preserve muscle mass, and minimize refined sugars.")
    elif "muscle" in query_lower or "weight gain" in query_lower or "bulk" in query_lower:
        return ("For healthy weight gain & muscle synthesis: Focus on complex carb sources (brown rice, oats, sweet potatoes), "
                "calorie-dense healthy fats (avocados, nuts, seeds), and a slight caloric surplus of 300-500 kcal.")
    elif "breakfast" in query_lower or "morning" in query_lower:
        return ("A balanced morning meal kickstarts your metabolism. Try combining complex carbohydrates with quality protein, "
                "such as Oatmeal with berries & chia seeds or a Veggie Egg White Omelet with whole grain toast.")
    elif "snack" in query_lower:
        return ("Healthy snack ideas: Handful of almonds & walnuts, Greek yogurt with honey, hummus with carrot sticks, "
                "or a low-sugar protein bar.")
    else:
        return (f"Based on your goal ({goal.title()}): Focus on whole foods, maintain consistent hydration, "
                "and ensure a balanced macronutrient ratio of protein, complex carbs, and healthy fats across your meals.")

def query_gemini(query_text, user_context=None):
    """
    Queries Google Gemini API using native urllib.request with fallback to local rule-based advisory engine.
    """
    user_context = user_context or {}
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    
    # If no key or placeholder, use intelligent fallback
    if not api_key or api_key == "YOUR-API-KEY":
        return generate_nutrition_fallback_response(query_text, user_context)

    url = f"{GEMINI_API_URL}?key={api_key}"
    
    prompt = "You are NutriMate AI, an expert certified dietitian & nutritionist. Provide clear, concise, actionable advice.\n"
    if user_context:
        prompt += f"User Metrics: Goal: {user_context.get('goal')}, Weight: {user_context.get('weight')}, Veg: {user_context.get('veg')}\n"
    prompt += f"User Question: {query_text}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                if 'candidates' in result and len(result['candidates']) > 0:
                    parts = result['candidates'][0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
    except Exception as e:
        print(f"Gemini API request error: {e}")
    
    return generate_nutrition_fallback_response(query_text, user_context)
