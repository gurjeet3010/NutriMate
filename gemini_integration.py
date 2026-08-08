import os
import re
import json
import urllib.request
import urllib.error

# Load .env file automatically if present
def load_dotenv_custom():
    global GEMINI_API_KEY, GEMINI_API_URL
    env_paths = ['.env', os.path.join(os.path.dirname(__file__), '.env')]
    for path in env_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k:
                                os.environ[k] = v
                                if k == "GEMINI_API_KEY":
                                    GEMINI_API_KEY = v
                                elif k == "GEMINI_API_URL":
                                    GEMINI_API_URL = v
            except Exception as e:
                print(f"Notice reading .env file: {e}")

GEMINI_API_KEY = ""
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
load_dotenv_custom()

# Comprehensive nutrition database for quick intelligent local retrieval
FOOD_KNOWLEDGE = {
    "egg": "1 large egg contains ~72 calories, 6.3g protein, 0.4g carbs, and 4.8g healthy fats (with choline, vitamin B12, and selenium).",
    "eggs": "2 large eggs provide ~144 calories, 12.6g high-biological-value protein, and essential micronutrients like choline, lutein, and vitamin D.",
    "oat": "1 cup of cooked oatmeal (approx. 234g) provides ~158 calories, 6g protein, 27g complex carbs, 4g dietary fiber (beta-glucan), and 3g healthy fats.",
    "oatmeal": "1 cup of cooked oatmeal (approx. 234g) provides ~158 calories, 6g protein, 27g complex carbs, 4g dietary fiber (beta-glucan), and 3g healthy fats.",
    "salmon": "100g of grilled salmon contains ~206 calories, 22g protein, 0g carbs, and 12g healthy fats (rich in anti-inflammatory EPA/DHA Omega-3s).",
    "chicken": "100g of skinless, cooked chicken breast contains ~165 calories, 31g pure protein, 0g carbs, and 3.6g fat.",
    "chicken breast": "100g of skinless, cooked chicken breast contains ~165 calories, 31g pure protein, 0g carbs, and 3.6g fat.",
    "apple": "1 medium apple (approx. 182g) has ~95 calories, 0.5g protein, 25g carbohydrates (including 4.4g soluble fiber and prebiotic pectin), and 0.3g fat.",
    "banana": "1 medium banana (approx. 118g) contains ~105 calories, 1.3g protein, 27g carbohydrates, 3.1g fiber, and 422mg of potassium.",
    "avocado": "1/2 medium avocado (approx. 100g) contains ~160 calories, 2g protein, 8.5g carbs (6.7g fiber), and 14.7g heart-healthy monounsaturated fats.",
    "greek yogurt": "100g of non-fat Greek yogurt delivers ~59 calories, 10g protein, 3.6g carbs, and gut-healthy active live probiotic cultures.",
    "yogurt": "1 cup (245g) of plain low-fat yogurt has ~154 calories, 13g protein, 17g carbs, and 3.8g fat, along with 450mg calcium.",
    "paneer": "100g of fresh paneer contains ~265 calories, 18.3g protein, 3.4g carbs, 20.8g fat, and 208mg calcium.",
    "tofu": "100g of firm tofu contains ~83 calories, 10g plant protein, 2g carbs, 5g healthy fats, and 282mg calcium.",
    "rice": "1 cup of cooked white rice provides ~205 calories, 4.2g protein, 45g carbs, and 0.4g fat. Brown rice provides ~216 calories with 3.5g fiber.",
    "brown rice": "1 cup of cooked brown rice provides ~216 calories, 5g protein, 45g complex carbs, 3.5g fiber, and essential magnesium.",
    "quinoa": "1 cup of cooked quinoa (185g) contains ~222 calories, 8.1g complete protein (all 9 essential amino acids), 39g carbs, and 5.2g fiber.",
    "lentils": "1 cup of cooked lentils (198g) provides ~230 calories, 17.9g plant-based protein, 40g carbs (including 15.6g fiber), and 37% daily iron.",
    "almonds": "1 ounce of almonds (approx. 23 nuts / 28g) provides ~164 calories, 6g protein, 6g carbs (3.5g fiber), and 14g healthy fats with 7.3mg vitamin E.",
    "walnuts": "1 ounce of walnuts (approx. 14 halves / 28g) provides ~185 calories, 4.3g protein, 3.9g carbs, and 18.5g fats (rich in ALA plant Omega-3s).",
    "peanut butter": "2 tablespoons (32g) of natural peanut butter provide ~190 calories, 8g protein, 7g carbs (2g fiber), and 16g healthy monounsaturated fats.",
    "whey": "1 scoop (30g) of standard whey protein isolate contains ~110-120 calories, 24-27g protein, <1g carbs, <1g fat, and ~5.5g BCAAs.",
    "milk": "1 cup (240ml) of whole milk contains ~149 calories, 8g protein, 12g carbs, 8g fat, and 300mg calcium. Skim milk has ~83 calories and 8.3g protein.",
}


def parse_and_convert_units(query_text):
    """
    Detects and calculates unit conversion requests (height, weight, energy, volume).
    Returns formatted string if conversion is detected, otherwise None.
    """
    q = query_text.lower().strip()
    
    # 1. Height conversions: Compound Feet & Inches (e.g. "5 ft 2 in", "5'2", "5 feet 2 inches")
    m_ft_in = re.search(r'(\d+)\s*(?:ft|feet|\'|foot)\s*(\d+(?:\.\d+)?)\s*(?:in|inch|inches|\"|in\b)?', q)
    if m_ft_in and ("cm" in q or "convert" in q or "into" in q or "to" in q or "in cm" in q):
        ft = float(m_ft_in.group(1))
        inches = float(m_ft_in.group(2))
        total_inches = (ft * 12) + inches
        cm_val = total_inches * 2.54
        return f"📐 **Height Conversion:**\n• **{int(ft)} ft {inches:g} in** ({ft + inches/12:.2f} ft) = **{cm_val:.2f} cm** (approx. {round(cm_val)} cm)\n*(Formula: (feet × 12 + inches) × 2.54 = cm)*"

    # Pattern b: Decimal feet (e.g. "5.2 ft", "5.8 feet to cm")
    m_ft_dec = re.search(r'(\d+(?:\.\d+)?)\s*(?:ft|feet|foot)\s*(?:into|to|in)?\s*(?:cm|centimeters|centimetres)?', q)
    if m_ft_dec and ("cm" in q or "convert" in q or "in cm" in q or "into cm" in q or "centimeter" in q):
        feet_val = float(m_ft_dec.group(1))
        cm_val = feet_val * 30.48
        return f"📐 **Height Conversion:**\n• **{feet_val:g} ft** = **{cm_val:.2f} cm** (approx. {round(cm_val)} cm)\n*(Formula: feet × 30.48 = cm)*"

    # Height conversions: CM into Feet / Inches
    m_cm = re.search(r'(\d+(?:\.\d+)?)\s*(?:cm|centimeters|centimetres)\s*(?:into|to|in)?\s*(?:ft|feet|foot|inches)?', q)
    if m_cm and ("ft" in q or "feet" in q or "inch" in q or "convert" in q):
        cm_val = float(m_cm.group(1))
        total_inches = cm_val / 2.54
        feet = int(total_inches // 12)
        rem_inches = total_inches % 12
        dec_feet = cm_val / 30.48
        return f"📐 **Height Conversion:**\n• **{cm_val:g} cm** = **{feet} ft {rem_inches:.1f} in** ({dec_feet:.2f} feet)\n*(Formula: cm ÷ 30.48 = feet)*"

    # 2. Weight conversions: KG to LBS
    m_kg = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilo|kilograms|kilos)\s*(?:into|to|in)?\s*(?:lbs|lb|pounds|pound)?', q)
    if m_kg and ("lb" in q or "pound" in q or "convert" in q):
        kg_val = float(m_kg.group(1))
        lbs_val = kg_val * 2.20462
        return f"⚖️ **Weight Conversion:**\n• **{kg_val:g} kg** = **{lbs_val:.2f} lbs** (pounds)\n*(Formula: kg × 2.20462 = lbs)*"

    # Weight conversions: LBS to KG
    m_lbs = re.search(r'(\d+(?:\.\d+)?)\s*(?:lbs|lb|pounds|pound)\s*(?:into|to|in)?\s*(?:kg|kgs|kilo|kilograms)?', q)
    if m_lbs and ("kg" in q or "kilo" in q or "convert" in q):
        lbs_val = float(m_lbs.group(1))
        kg_val = lbs_val / 2.20462
        return f"⚖️ **Weight Conversion:**\n• **{lbs_val:g} lbs** = **{kg_val:.2f} kg** (kilograms)\n*(Formula: lbs ÷ 2.20462 = kg)*"

    # 3. Energy: Calories / kcal to kJ
    m_cal = re.search(r'(\d+(?:\.\d+)?)\s*(?:kcal|calories|cal)\s*(?:into|to|in)?\s*(?:kj|kilojoules)?', q)
    if m_cal and ("kj" in q or "joule" in q):
        cal_val = float(m_cal.group(1))
        kj_val = cal_val * 4.184
        return f"⚡ **Energy Conversion:**\n• **{cal_val:g} kcal** = **{kj_val:.2f} kJ** (kilojoules)\n*(Formula: kcal × 4.184 = kJ)*"

    return None


def calculate_health_metrics(query_text, user_context=None):
    """
    Computes BMI, TDEE, BMR, water targets, or protein targets from text or user context.
    """
    user_context = user_context or {}
    q = query_text.lower()

    # Extract weight & height if present in the message
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilos)', q)
    height_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cm|centimeters)', q)
    
    weight = float(weight_match.group(1)) if weight_match else float(user_context.get("weight") or 70)
    height = float(height_match.group(1)) if height_match else float(user_context.get("height") or 170)
    age = int(user_context.get("age") or 25)
    goal = str(user_context.get("goal") or "Healthy").title()

    # BMI calculation
    if "bmi" in q or "body mass index" in q:
        height_m = height / 100.0
        bmi = weight / (height_m ** 2) if height_m > 0 else 22.0
        
        if bmi < 18.5:
            category = "Underweight ⚠️"
            advice = "Focus on a nutrient-rich caloric surplus (+300 to +500 kcal/day) with complex carbs, healthy fats, and strength training."
        elif 18.5 <= bmi < 25.0:
            category = "Normal / Healthy Weight ✅"
            advice = "Great job! Maintain your balanced nutrition, consistent hydration, and active lifestyle."
        elif 25.0 <= bmi < 30.0:
            category = "Overweight 🟡"
            advice = "Aim for a moderate caloric deficit (-300 to -500 kcal/day), increase lean protein & dietary fiber, and aim for 150+ minutes of weekly activity."
        else:
            category = "Obese (Class I/II) 🔴"
            advice = "Prioritize whole foods, fiber-dense vegetables, caloric tracking, and consult your healthcare professional for personalized guidance."

        return (f"📊 **BMI Calculation for {weight:.1f} kg & {height:.0f} cm:**\n"
                f"• **Your BMI:** **{bmi:.1f}** ({category})\n"
                f"• **Healthy BMI Range:** 18.5 – 24.9\n"
                f"• **Dietitian Guidance:** {advice}")

    # BMR & TDEE calculation
    if "bmr" in q or "tdee" in q or "maintenance calories" in q or "calorie requirement" in q or "daily calories" in q:
        # Mifflin-St Jeor Formula (General average)
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        tdee_sedentary = bmr * 1.2
        tdee_moderate = bmr * 1.55
        tdee_active = bmr * 1.725
        
        return (f"🔥 **Estimated Metabolic Energy Needs:**\n"
                f"• **Basal Metabolic Rate (BMR):** ~{round(bmr)} kcal/day (energy burned at complete rest)\n"
                f"• **TDEE (Moderate Activity):** ~{round(tdee_moderate)} kcal/day\n"
                f"• **For Weight Loss:** ~{round(tdee_moderate - 400)} kcal/day (400 kcal deficit)\n"
                f"• **For Muscle Gain:** ~{round(tdee_moderate + 350)} kcal/day (350 kcal surplus)")

    # Water requirement
    if "water" in q or "hydration" in q or "liters" in q or "litres" in q or "drink" in q:
        water_min = (weight * 35) / 1000.0  # 35ml per kg
        water_max = (weight * 45) / 1000.0  # 45ml per kg if active
        return (f"💧 **Personalized Daily Hydration Target:**\n"
                f"• **Recommended Intake:** **{water_min:.1f} to {water_max:.1f} Liters / day** (~{round(water_min * 4)} standard 250ml glasses)\n"
                f"• **Dietitian Tip:** Drink 1 glass of water 20 minutes before meals to optimize digestion and satiety. Increase intake during workouts.")

    # Protein requirement target
    if "how much protein" in q or "protein target" in q or "protein requirement" in q or "protein intake" in q or "calculate protein" in q or "daily protein" in q:
        p_min = weight * 1.2
        p_max = weight * 2.0
        return (f"🥩 **Daily Protein Intake Guidance:**\n"
                f"• **Target Range:** **{p_min:.0f}g – {p_max:.0f}g** per day ({1.2}g – {2.0}g per kg of body weight)\n"
                f"• **Vegetarian Sources:** Greek yogurt ({10}g/100g), Paneer ({18}g/100g), Firm Tofu ({10}g/100g), Lentils ({18}g/cup), Quinoa ({8}g/cup).\n"
                f"• **Non-Vegetarian Sources:** Chicken breast ({31}g/100g), Salmon ({22}g/100g), Whole Eggs ({6}g/egg), Tuna ({26}g/100g).")

    return None


def generate_nutrition_fallback_response(query_text, user_context=None):
    """
    Intelligent NLP & Dietary Rules Engine:
    Handles unit conversions, calculations, food lookups, macro advice,
    and structured nutrition responses locally without external API dependencies.
    """
    user_context = user_context or {}
    q = (query_text or "").strip().lower()
    goal = str(user_context.get("goal", "Healthy Maintenance")).title()

    # 1. Check for Unit Conversions
    conv_result = parse_and_convert_units(query_text)
    if conv_result:
        return conv_result

    # 2. Check for Health & Metric Calculations
    metric_result = calculate_health_metrics(query_text, user_context)
    if metric_result:
        return metric_result

    # 3. Check for specific food lookups in our nutritional database
    for food_key, info in FOOD_KNOWLEDGE.items():
        if re.search(r'\b' + re.escape(food_key) + r'\b', q):
            return f"🥗 **Nutritional Profile: {food_key.title()}**\n{info}\n\n💡 *Fits well into your {goal} meal plan!*"

    # 4. Contextual Dietary Advice Categorization
    if "weight loss" in q or "lose weight" in q or "fat loss" in q or "deficit" in q or "cutting" in q:
        return ("📉 **Sustainable Weight Loss Strategy:**\n"
                "1. **Caloric Deficit:** Aim for 300–500 kcal below your TDEE for steady 0.5kg/week fat loss.\n"
                "2. **High Protein:** Consume 1.6–2.0g protein/kg to protect lean muscle mass during deficit.\n"
                "3. **Volume Eating:** Fill half your plate with leafy greens, broccoli, and fibrous vegetables.\n"
                "4. **Smart Carbs:** Opt for oats, quinoa, and berries over refined sugars to prevent insulin spikes.")

    elif "muscle" in q or "weight gain" in q or "bulk" in q or "hypertrophy" in q:
        return ("🏋️ **Muscle Gain & Lean Bulking Protocol:**\n"
                "1. **Caloric Surplus:** Maintain a moderate 300–400 kcal surplus above maintenance.\n"
                "2. **Protein Target:** Consume 1.6–2.2g of protein per kg of body weight distributed across 3–4 meals.\n"
                "3. **Complex Energy:** Fuel workouts with sweet potatoes, brown rice, whole oats, and bananas.\n"
                "4. **Healthy Fats:** Include avocados, peanut butter, and almonds for calorie density and hormonal health.")

    elif "intermittent fasting" in q or "fasting" in q or "16/8" in q:
        return ("⏳ **Intermittent Fasting (16/8 Method):**\n"
                "• **Structure:** 16-hour fasting window (water, black coffee, green tea only) + 8-hour feeding window (e.g., 12 PM – 8 PM).\n"
                "• **Key Benefits:** Improved insulin sensitivity, cellular autophagy, and simplified caloric control.\n"
                "• **Caution:** Ensure you hit your complete daily protein and micronutrient targets during feeding hours.")

    elif "pre workout" in q or "pre-workout" in q or "before gym" in q:
        return ("⚡ **Pre-Workout Fuel (30–60 mins prior):**\n"
                "• Combine fast-digesting complex carbs with a touch of protein:\n"
                "  - 1 Banana with 1 tbsp peanut butter\n"
                "  - Oatmeal with blueberries and a scoop of protein\n"
                "  - 2 slices of whole wheat toast with honey\n"
                "• Drink 400–500ml water to ensure muscle hydration and endurance.")

    elif "post workout" in q or "post-workout" in q or "after gym" in q:
        return ("🔄 **Post-Workout Recovery (within 45 mins):**\n"
                "• **Protein Synthesis:** 25–35g high-quality protein (Whey isolate, Greek yogurt, or Egg whites/Tofu).\n"
                "• **Glycogen Replenishment:** 30–50g fast/moderate carbs (Rice cakes, fruit, or oats).\n"
                "• Replenish lost electrolytes (sodium, potassium) with water and coconut water.")

    elif "keto" in q or "ketogenic" in q or "low carb" in q:
        return ("🥑 **Keto / Low-Carb Nutrition:**\n"
                "• **Macronutrient Split:** ~70% Healthy Fats, 25% Protein, 5% Net Carbs (<30g/day).\n"
                "• **Primary Staples:** Avocados, eggs, salmon, olive oil, walnuts, spinach, and paneer/cheese.\n"
                "• **Electrolyte Balance:** Supplement sodium, potassium, and magnesium to prevent keto flu.")

    elif "vegan" in q or "vegetarian" in q or "plant based" in q:
        return ("🌱 **Plant-Based Protein Optimization:**\n"
                "• Combine complementary proteins to ensure complete amino acid profiles:\n"
                "  - Rice + Lentils / Dal (complete protein profile)\n"
                "  - Quinoa bowls with edamame & hemp seeds\n"
                "  - Firm Tofu stir-fry with broccoli and peanuts\n"
                "• Consider Vitamin B12 and Vitamin D3 supplementation.")

    elif "diabetes" in q or "sugar" in q or "glucose" in q or "glycemic" in q:
        return ("🩺 **Blood Sugar Management Diet:**\n"
                "• **Low Glycemic Index (GI):** Steel-cut oats, lentils, non-starchy vegetables, and berries.\n"
                "• **Fiber Pairing:** Always pair carbohydrates with healthy fats or protein to slow gastric emptying.\n"
                "• Avoid sugary sodas, refined white flour, and fruit juices with added sugar.")

    elif "hypertension" in q or "blood pressure" in q or "bp" in q or "sodium" in q:
        return ("❤️ **DASH Diet & Blood Pressure Care:**\n"
                "• Keep daily sodium under 2,000mg; use fresh herbs and lemon juice for seasoning.\n"
                "• Boost potassium and magnesium: Spinach, bananas, sweet potatoes, and unroasted pumpkin seeds.\n"
                "• Stay consistent with 2.5–3.0 liters of daily hydration.")

    elif "snack" in q or "snacks" in q or "craving" in q:
        return ("🍎 **Nutrient-Dense Healthy Snacks (<200 kcal):**\n"
                "• 1 cup Greek yogurt with fresh berries\n"
                "• Apple slices with 1 tbsp peanut butter\n"
                "• Hummus (3 tbsp) with crunchy cucumber and carrot sticks\n"
                "• Handful of roasted almonds and walnuts (30g)")

    elif "breakfast" in q or "morning" in q:
        return ("🌅 **Metabolism-Boosting Breakfast Ideas:**\n"
                "• **Option 1 (Quick & Energizing):** Oatmeal topped with chia seeds, blueberries, and walnuts.\n"
                "• **Option 2 (High Protein):** 3 Egg White Omelet with spinach & mushrooms on 1 slice whole grain toast.\n"
                "• **Option 3 (Plant Protein):** Tofu scramble with bell peppers and avocado toast.")

    # 5. Default intelligent response personalized to user context
    return (f"🥗 **NutriMate Personalized Nutrition Insight:**\n"
            f"• **Your Active Goal:** **{goal}**\n"
            f"• **Key Focus:** Focus on nutrient-dense whole foods, maintain consistent hydration (~{round((float(user_context.get('weight') or 70)*35)/1000, 1)}L/day), "
            f"and balance your plate with 40% complex carbs, 30% lean protein, and 30% healthy fats.\n"
            f"• *Tip: You can ask me to calculate BMI, convert units (e.g. 'convert 5.2 ft into cm' or '70 kg to lbs'), or look up food calories!*")


def query_gemini(query_text, user_context=None):
    """
    Queries Google Gemini API using native urllib.request with seamless fallback
    to our comprehensive local intelligent calculation & nutrition engine.
    """
    user_context = user_context or {}
    api_key = (os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY or "").strip()

    # If no valid API key is set, use the built-in intelligent engine
    if not api_key or api_key == "YOUR-API-KEY" or len(api_key) < 15:
        return generate_nutrition_fallback_response(query_text, user_context)

    # Unit conversion and simple math are best handled instantly locally
    quick_calc = parse_and_convert_units(query_text)
    if quick_calc:
        return quick_calc

    prompt = (
        "You are NutriMate AI, an expert certified clinical dietitian, nutritionist, and fitness consultant. "
        "Provide clear, concise, actionable, and encouraging nutrition advice formatted with markdown bullet points.\n\n"
    )
    if user_context:
        prompt += (
            f"User Profile: Goal: {user_context.get('goal', 'Healthy')}, "
            f"Weight: {user_context.get('weight', 70)}kg, "
            f"Height: {user_context.get('height', 170)}cm, "
            f"Diet: {'Vegetarian' if user_context.get('veg') == 1 else 'Non-Vegetarian'}\n\n"
        )
    prompt += f"User Question: {query_text}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }
    data = json.dumps(payload).encode('utf-8')

    # Attempt Google Gemini API models in priority order
    models_to_try = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    ]
    
    for endpoint in models_to_try:
        url = f"{endpoint}?key={api_key}"
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    if 'candidates' in result and len(result['candidates']) > 0:
                        parts = result['candidates'][0].get('content', {}).get('parts', [])
                        if parts and 'text' in parts[0]:
                            return parts[0]['text']
        except urllib.error.HTTPError as he:
            err_body = he.read().decode('utf-8', errors='ignore') if hasattr(he, 'read') else str(he)
            model_name = endpoint.split('/')[-1].split(':')[0]
            print(f"Gemini API model {model_name} notice ({he.code}): {err_body[:120]}")
            if he.code == 400 and "API_KEY_INVALID" in err_body:
                # Key is invalid, stop trying models
                break
        except Exception as e:
            print(f"Gemini API connection notice: {e}")
    
    return generate_nutrition_fallback_response(query_text, user_context)
