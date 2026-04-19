import json

# -------------------------------
# LOAD FILES
# -------------------------------
with open("kundali_rebuilt.json", "r") as f:
    kundali = json.load(f)

with open("filtered_chunks.json", "r") as f:
    chunks = json.load(f)

planets = kundali["planets"]
dasha = kundali.get("Vimshottari_Dasha", [])
sadesati = kundali.get("SadeSati", [])

# -------------------------------
# SMART RETRIEVAL (UPGRADED)
# -------------------------------
def retrieve_insights(keywords, chunk_list=None):
    if chunk_list is None:
        chunk_list = chunks

    scored = []

    for chunk in chunk_list:
        text = chunk.get("text", "").lower()

        score = 0

        # strong keyword match
        for k in keywords:
            if k in text:
                score += 2

        # logic words bonus
        logic_words = ["house", "effect", "result", "indicates", "gives", "causes"]
        for lw in logic_words:
            if lw in text:
                score += 1

        if score >= 3:
            scored.append((score, chunk["text"]))

    scored.sort(reverse=True, key=lambda x: x[0])

    return [text for _, text in scored[:5]]


# -------------------------------
# INTERPRETATION LAYER
# -------------------------------
def interpret_text(raw_text):
    text = raw_text.strip()

    # Remove noisy OCR patterns
    if any(x in text.lower() for x in [
        "page", "chapter", "pdf", "copyright",
        "vedic remedies in astrology", "brihat parasara"
    ]):
        return None

    # Clean formatting
    text = text.replace("\n", " ").strip()

    # Skip too short or broken text
    if len(text) < 40:
        return None

    # Convert into Jyotish-style interpretation
    return f"This indicates that {text.lower().capitalize()}."


# -------------------------------
# PLANET ANALYSIS
# -------------------------------
def analyze_planets():
    output = []

    for planet, data in planets.items():
        keywords = [
            planet.lower(),
            data.get("sign", "").lower(),
            data.get("nakshatra", "").lower(),
            f"house {data.get('house', '')}"
        ]

        insights = retrieve_insights(keywords)

        section = f"\n=== {planet.upper()} ===\n"
        section += f"{planet} in {data.get('sign', 'N/A')} (House {data.get('house', 'N/A')}, {data.get('nakshatra', 'N/A')})\n"

        for insight in insights:
            interpreted = interpret_text(insight)
            if interpreted:
                section += f"- {interpreted}\n"

        output.append(section)

    return "\n".join(output)


# -------------------------------
# MAHADASHA ANALYSIS
# -------------------------------
def analyze_dasha():
    output = "\n=== MAHADASHA ANALYSIS ===\n"

    for period in dasha[:3]:
        planet = period.get("planet", "Unknown")

        keywords = [
            planet.lower(),
            "dasha",
            "mahadasa",
            "effects"
        ]

        insights = retrieve_insights(keywords)

        output += f"\n{planet} Mahadasha ({period.get('start', '?')} - {period.get('end', '?')}):\n"

        for insight in insights:
            interpreted = interpret_text(insight)
            if interpreted:
                output += f"- {interpreted}\n"

    return output


# -------------------------------
# SADE SATI ANALYSIS
# -------------------------------
def analyze_sadesati():
    output = "\n=== SADE SATI ANALYSIS ===\n"
    output += "Sade Sati is a transit-based influence and should be interpreted along with Dasha and Yogas.\n\n"

    for period in sadesati:
        if period.get("type") == "Sade Sati":
            keywords = [
                "saturn",
                "sade sati",
                period.get("rashi", "").lower()
            ]

            insights = retrieve_insights(keywords)

            output += f"\n{period.get('phase', '?')} Phase ({period.get('start', '?')} - {period.get('end', '?')}):\n"

            for insight in insights:
                interpreted = interpret_text(insight)
                if interpreted:
                    output += f"- {interpreted}\n"

    return output


# -------------------------------
# YOGA DETECTION
# -------------------------------
def detect_yogas():
    output = "\n=== YOGA INDICATIONS ===\n"

    keywords = [
        "yoga",
        "raj yoga",
        "dhan yoga",
        "vipreet",
        "lakshmi yoga"
    ]

    insights = retrieve_insights(keywords)

    for insight in insights:
        interpreted = interpret_text(insight)
        if interpreted:
            output += f"- {interpreted}\n"

    return output


# -------------------------------
# DRISHTI (ASPECTS)
# -------------------------------
SIGN_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Special additional aspects (houses counted from planet's house, 1-based)
SPECIAL_ASPECTS = {
    "Mars":    [4, 8],
    "Jupiter": [5, 9],
    "Saturn":  [3, 10],
    "Rahu":    [5, 9],
    "Ketu":    [5, 9],
}


def _sign_index(sign):
    try:
        return SIGN_ORDER.index(sign)
    except ValueError:
        return -1


def _house_to_sign(from_sign, houses_away):
    idx = _sign_index(from_sign)
    if idx == -1:
        return None
    return SIGN_ORDER[(idx + houses_away - 1) % 12]


def calculate_aspects(planet_data):
    results = []
    for planet, data in planet_data.items():
        sign = data.get("sign", "")
        aspected_signs = []

        # All planets aspect the 7th sign (opposition)
        seventh = _house_to_sign(sign, 7)
        if seventh:
            aspected_signs.append((7, seventh))

        # Special aspects
        for houses_away in SPECIAL_ASPECTS.get(planet, []):
            asp_sign = _house_to_sign(sign, houses_away)
            if asp_sign:
                aspected_signs.append((houses_away, asp_sign))

        for h, asp_sign in aspected_signs:
            aspected_planets = [
                p for p, d in planet_data.items()
                if d.get("sign") == asp_sign and p != planet
            ]
            desc = f"{planet} ({sign}) aspects {asp_sign} (house-{h} drishti)"
            if aspected_planets:
                desc += f" — aspecting {', '.join(aspected_planets)}"
            results.append(desc)

    return results


# -------------------------------
# NAVAMSA (D9)
# -------------------------------
# First navamsa sign for each element group
_NAVAMSA_START = {
    "fire":  0,   # Aries
    "earth": 9,   # Capricorn
    "air":   6,   # Libra
    "water": 3,   # Cancer
}

_SIGN_ELEMENT = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}


def calculate_navamsa(degree, sign):
    """Return the Navamsa (D9) sign for a planet at *degree* in *sign*."""
    element = _SIGN_ELEMENT.get(sign)
    if element is None:
        return "Unknown"

    # Which 3°20' segment within the sign? (0-8)
    segment = int(degree / (30.0 / 9))
    segment = min(segment, 8)

    start_idx = _NAVAMSA_START[element]
    navamsa_idx = (start_idx + segment) % 12
    return SIGN_ORDER[navamsa_idx]


# -------------------------------
# IMPROVED SHADBALA
# -------------------------------
_EXALTATION = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
    "Saturn": "Libra",
}
_DEBILITATION = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
    "Saturn": "Aries",
}
_OWN_SIGN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
    "Rahu": [], "Ketu": [],
}
# Directional strength: planet → house of max dik-bala
_DIK_BALA_HOUSE = {
    "Sun": 10, "Mars": 10, "Jupiter": 1, "Mercury": 1,
    "Moon": 4, "Venus": 4, "Saturn": 7,
}


def improved_shadbala(planet_data):
    results = []
    for planet, data in planet_data.items():
        sign = data.get("sign", "")
        house = data.get("house", 0)
        score = 0
        notes = []

        # Sthana bala (positional strength)
        if _EXALTATION.get(planet) == sign:
            score += 60
            notes.append("exalted")
        elif _DEBILITATION.get(planet) == sign:
            score -= 30
            notes.append("debilitated")
        elif sign in _OWN_SIGN.get(planet, []):
            score += 45
            notes.append("own sign")

        # Dik bala (directional strength)
        best_house = _DIK_BALA_HOUSE.get(planet)
        if best_house is not None and house == best_house:
            score += 30
            notes.append("full dik-bala")
        elif best_house is not None and abs(house - best_house) <= 2:
            score += 15
            notes.append("partial dik-bala")

        # Kendra/trikona bonus (angular/trine houses strengthen planets)
        if house in (1, 4, 7, 10):
            score += 20
            notes.append("kendra")
        elif house in (5, 9):
            score += 15
            notes.append("trikona")

        # Dusthana penalty (6, 8, 12)
        if house in (6, 8, 12):
            score -= 20
            notes.append("dusthana")

        label = "Strong" if score >= 60 else ("Moderate" if score >= 20 else "Weak")
        tag = ", ".join(notes) if notes else "neutral"
        results.append(f"{planet}: Shadbala score = {score} [{label}] ({tag})")

    return results


# -------------------------------
# TRANSIT LOGIC (SATURN)
# -------------------------------
def saturn_transit_effect(planet_data):
    moon_sign = planet_data.get("Moon", {}).get("sign", "")
    saturn_sign = planet_data.get("Saturn", {}).get("sign", "")

    if not moon_sign or not saturn_sign:
        return "Transit data unavailable (Moon or Saturn sign missing)."

    moon_idx = _sign_index(moon_sign)
    saturn_idx = _sign_index(saturn_sign)

    if moon_idx == -1 or saturn_idx == -1:
        return "Transit data unavailable (unrecognized sign)."

    # Difference in signs (forward count from Moon)
    diff = (saturn_idx - moon_idx) % 12 + 1  # 1-based house from Moon

    output = f"Saturn transiting {saturn_sign}, natal Moon in {moon_sign} (Saturn in {diff}th from Moon).\n"

    sade_sati_houses = {12, 1, 2}
    ashtama_houses = {8}
    if diff in sade_sati_houses:
        output += "⚠  SADE SATI active — period of challenges, introspection, and karmic lessons."
    elif diff in ashtama_houses:
        output += "⚠  ASHTAMA SHANI active — pressure on health, finances, and stability."
    elif diff in {4, 7, 10}:
        output += "⚡ Kantaka Shani (square transit) — obstacles in career and relationships possible."
    elif diff in {3, 6, 11}:
        output += "✅ Favourable Saturn transit — discipline and hard work bring rewards."
    else:
        output += "Saturn transit effect is neutral for the current period."

    return output


# -------------------------------
# DOSHA DETECTION
# -------------------------------
def detect_doshas(planet_data):
    output = "\n=== DOSHA ANALYSIS ===\n"
    output += "This section identifies key karmic patterns in your chart that may influence important life areas.\n\n"

    mars_house = planet_data.get("Mars", {}).get("house")
    if mars_house in [1, 4, 7, 8, 12]:
        output += "Your chart carries Manglik Dosha — this placement of Mars may influence your marriage dynamics and should be considered when making partnership decisions.\n"

    rahu_house = planet_data.get("Rahu", {}).get("house")
    ketu_house = planet_data.get("Ketu", {}).get("house")
    if rahu_house == 1 and ketu_house == 7:
        output += "A Kaal Sarp pattern is detected in your chart — your life journey may feature dramatic highs and lows, but these experiences ultimately shape profound inner growth.\n"

    return output


# -------------------------------
# FINAL SYNTHESIS / PREDICTION
# -------------------------------
def generate_final_prediction(planet_data, dasha_list, transit_text):
    output = "\n=== FINAL PREDICTION ===\n"
    output += "Based on the full analysis of your chart, here is a synthesised view of what lies ahead.\n\n"

    # Career logic based on Saturn placement
    if "Saturn" in planet_data:
        house = planet_data["Saturn"].get("house")
        if house in [10, 11]:
            output += "Your chart indicates that your career is likely to grow steadily over time, especially through discipline and persistence.\n"
        elif house in [6, 8, 12]:
            output += "Your chart suggests possible career delays and struggles, but long-term stability is very much attainable with patience and consistent effort.\n"

    # Moon sign emotional nature
    moon_sign = planet_data.get("Moon", {}).get("sign")
    if moon_sign:
        output += f"Your emotional tendencies are influenced by {moon_sign}, shaping the way you process and make important decisions in life.\n"

    # Dasha influence
    if len(dasha_list) > 0:
        current = dasha_list[0].get("planet", "")
        output += f"The current Mahadasha of {current} is set to dominate key life events and themes during this period.\n"

    # Transit influence
    output += transit_text + "\n"

    return output


# -------------------------------
# COMBINED SYNTHESIS ANALYSIS
# -------------------------------
def combined_analysis(planet_data):
    output = "\n=== COMBINED ANALYSIS ===\n"
    output += "This section looks at planetary combinations in your chart that produce distinctive life themes and outcomes.\n\n"

    if (planet_data.get("Saturn", {}).get("house") == 12
            and planet_data.get("Jupiter", {}).get("house") == 12):
        output += "With both Saturn and Jupiter placed in the 12th house, your chart carries strong spiritual potential along with meaningful connections to foreign lands or institutions.\n"

    if planet_data.get("Sun", {}).get("house") == 3:
        output += "Your Sun in the 3rd house bestows courage and a natural ability to lead through communication, writing, and self-driven effort.\n"

    return output


# -------------------------------
# ANTARDASHA ANALYSIS
# -------------------------------
def analyze_antardasha(dasha_list):
    output = "\n=== ANTARDASHA ANALYSIS ===\n"
    output += "This section analyzes sub-period influences within the current Mahadasha.\n\n"

    if len(dasha_list) < 2:
        return output + "Insufficient data for Antardasha analysis.\n"

    main = dasha_list[0].get("planet", "")
    sub = dasha_list[1].get("planet", "")

    output += f"You are currently running {main}-{sub} period.\n"

    if main == "Saturn":
        output += "This period emphasizes discipline, responsibility, and karmic lessons.\n"

    if sub == "Mercury":
        output += "Sub-period of Mercury brings focus on communication, learning, and analytical thinking.\n"

    return output


# -------------------------------
# CLASSICAL YOGA DETECTION
# -------------------------------
def detect_real_yogas(planet_data):
    output = "\n=== CLASSICAL YOGA ANALYSIS ===\n"
    output += "This section identifies important yogas formed in your chart.\n\n"

    yoga_found = False

    # Raj Yoga: Kendra + Trikona lord interaction (simplified)
    if (planet_data.get("Jupiter", {}).get("house") in [1, 5, 9]
            and planet_data.get("Saturn", {}).get("house") in [1, 4, 7, 10]):
        output += "⚡ Raj Yoga indicates potential rise in status, authority, and recognition.\n"
        yoga_found = True

    # Dhan Yoga
    if (planet_data.get("Venus", {}).get("house") in [2, 11]
            or planet_data.get("Jupiter", {}).get("house") in [2, 11]):
        output += "💰 Dhan Yoga indicates financial growth and wealth accumulation potential.\n"
        yoga_found = True

    # Vipreet Raj Yoga
    if planet_data.get("Saturn", {}).get("house") in [6, 8, 12]:
        output += "🔥 Vipreet Raj Yoga indicates success through adversity and unexpected rise.\n"
        yoga_found = True

    if not yoga_found:
        output += "No major classical yogas detected, but planetary combinations still influence destiny.\n"

    return output


# -------------------------------
# CAREER ANALYSIS
# -------------------------------
def analyze_career(planet_data):
    output = "\n=== CAREER ANALYSIS ===\n"
    output += "This section evaluates professional direction, growth, and challenges.\n\n"

    saturn_house = planet_data.get("Saturn", {}).get("house")
    sun_house = planet_data.get("Sun", {}).get("house")

    if saturn_house in [10, 11]:
        output += "Strong long-term career growth with discipline and persistence.\n"

    if saturn_house in [6, 8, 12]:
        output += "Career may involve delays, struggles, or unconventional paths.\n"

    if sun_house == 10:
        output += "Sun in 10th gives leadership ability and authority in career.\n"

    return output


# -------------------------------
# MARRIAGE & RELATIONSHIP ANALYSIS
# -------------------------------
def analyze_marriage(planet_data):
    output = "\n=== MARRIAGE & RELATIONSHIP ANALYSIS ===\n"
    output += "This section evaluates partnership dynamics and marital prospects.\n\n"

    venus_house = planet_data.get("Venus", {}).get("house")
    mars_house = planet_data.get("Mars", {}).get("house")

    if venus_house in [7, 1]:
        output += "Strong indications for attraction, romance, and meaningful partnerships.\n"

    if mars_house in [7, 8]:
        output += "Mars influence suggests intensity in relationships — careful handling of conflicts is advised.\n"

    if planet_data.get("Saturn", {}).get("house") == 7:
        output += "Saturn in 7th may delay marriage but ensures stability and maturity.\n"

    return output


# -------------------------------
# CLASSICAL REMEDIES
# -------------------------------
def suggest_remedies(planet_data):
    output = "\n=== CLASSICAL REMEDIES ===\n"
    output += "These remedies are based on traditional Vedic practices.\n\n"

    if planet_data.get("Saturn"):
        output += "- Chant 'Om Sham Shanicharaya Namah' on Saturdays.\n"
        output += "- Donate black sesame seeds or mustard oil.\n"

    if planet_data.get("Mars"):
        output += "- Chant 'Om Angarakaya Namah'.\n"
        output += "- Visit Hanuman temple on Tuesdays.\n"

    if planet_data.get("Rahu"):
        output += "- Chant 'Om Rahave Namah'.\n"

    if planet_data.get("Ketu"):
        output += "- Chant 'Om Ketave Namah'.\n"

    return output


# -------------------------------
# SIGN CONSTANTS (shared by lord analysis functions)
# -------------------------------
SIGN_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter"
}


# -------------------------------
# ANTARDASHA TIMELINE
# -------------------------------
def antardasha_timeline(dasha_list):
    output = "\n=== ANTARDASHA TIMELINE ===\n"
    output += "Detailed breakdown of sub-periods within the current Mahadasha.\n\n"

    for d in dasha_list[:5]:
        planet = d.get("planet", "")
        start = d.get("start", "?")
        end = d.get("end", "?")

        output += f"{planet} Antardasha: {start} → {end}\n"

    return output


# -------------------------------
# LAGNA LORD ANALYSIS
# -------------------------------
def analyze_lagna_lord(kundali_data, planet_data):
    output = "\n=== LAGNA LORD ANALYSIS ===\n\n"

    lagna = kundali_data.get("ascendant", "")
    lord = SIGN_LORDS.get(lagna)

    if not lord:
        return output + "Lagna lord not found.\n"

    data = planet_data.get(lord, {})

    output += f"Your ascendant is {lagna}, ruled by {lord}.\n"
    output += f"{lord} is placed in {data.get('sign')} (House {data.get('house')}).\n"

    if data.get("house") in [1, 5, 9]:
        output += "This strengthens personality, confidence, and life direction.\n"
    elif data.get("house") in [6, 8, 12]:
        output += "This indicates challenges and karmic lessons shaping your life path.\n"

    return output


# -------------------------------
# 10TH LORD (CAREER DEEP ANALYSIS)
# -------------------------------
def analyze_10th_lord(planet_data, kundali_data):
    output = "\n=== 10TH LORD (CAREER DEEP ANALYSIS) ===\n\n"

    lagna = kundali_data.get("ascendant", "")
    if lagna not in SIGN_ORDER:
        return output + "Ascendant not found for 10th lord analysis.\n"

    lagna_index = SIGN_ORDER.index(lagna)
    tenth_sign = SIGN_ORDER[(lagna_index + 9) % 12]
    lord = SIGN_LORDS.get(tenth_sign)

    data = planet_data.get(lord, {})

    output += f"Your 10th house falls in {tenth_sign}, ruled by {lord}.\n"
    output += f"{lord} is placed in {data.get('sign')} (House {data.get('house')}).\n"

    if data.get("house") in [10, 11]:
        output += "Indicates strong professional success and recognition.\n"
    elif data.get("house") in [6, 8, 12]:
        output += "Career path may involve obstacles, transformation, or unconventional routes.\n"

    return output


# -------------------------------
# 7TH LORD (MARRIAGE DEEP ANALYSIS)
# -------------------------------
def analyze_7th_lord(planet_data, kundali_data):
    output = "\n=== 7TH LORD (MARRIAGE DEEP ANALYSIS) ===\n\n"

    lagna = kundali_data.get("ascendant", "")
    if lagna not in SIGN_ORDER:
        return output + "Ascendant not found for 7th lord analysis.\n"

    lagna_index = SIGN_ORDER.index(lagna)
    seventh_sign = SIGN_ORDER[(lagna_index + 6) % 12]
    lord = SIGN_LORDS.get(seventh_sign)

    data = planet_data.get(lord, {})

    output += f"Your 7th house falls in {seventh_sign}, ruled by {lord}.\n"
    output += f"{lord} is placed in {data.get('sign')} (House {data.get('house')}).\n"

    if data.get("house") in [1, 5, 7]:
        output += "Favorable for relationships and partnership harmony.\n"
    elif data.get("house") in [6, 8, 12]:
        output += "May indicate delays, challenges, or karmic patterns in relationships.\n"

    return output


# -------------------------------
# FINAL REPORT
# -------------------------------
def generate_report():
    print("\n🔱 VEDIC ASTROLOGY REPORT 🔱\n")

    # --- Task 5: Report Navigation ---
    print("\n=== REPORT STRUCTURE ===")
    print("1. Yogas → Core destiny")
    print("2. Dasha → Timing")
    print("3. Planets → Base structure")
    print("4. Transit → Temporary influence\n")

    # 1. Kundali Summary
    print("=== KUNDALI SUMMARY ===")
    for key in ("name", "date_of_birth", "time_of_birth", "place_of_birth", "ascendant"):
        if key in kundali:
            print(f"  {key.replace('_', ' ').title()}: {kundali[key]}")
    print()

    # Planetary placements
    print("=== PLANETARY PLACEMENTS ===")
    for planet, data in planets.items():
        print(f"  {planet:10s} | Sign: {data.get('sign', 'N/A'):15s} | House: {data.get('house', 'N/A'):2} | Nakshatra: {data.get('nakshatra', 'N/A')}")
    print()

    # 2. Classical Yogas
    print("\n🔥 CORE DESTINY FACTORS (YOGAS) 🔥\n")
    print(detect_real_yogas(planets))

    # 3. Lagna Lord Analysis
    print(analyze_lagna_lord(kundali, planets))

    # 4. 10th Lord (Career Core)
    print(analyze_10th_lord(planets, kundali))

    # 5. 7th Lord (Marriage Core)
    print(analyze_7th_lord(planets, kundali))

    # 6. Planetary Analysis
    print(analyze_planets())

    # 7. Mahadasha Analysis
    print("\n⏳ TIMING ANALYSIS (DASHA SYSTEM) ⏳\n")
    print(analyze_dasha())

    # 8. Antardasha Analysis
    print(analyze_antardasha(dasha))

    # 9. Antardasha Timeline
    print(antardasha_timeline(dasha))

    # 10. Combined Analysis
    print(combined_analysis(planets))

    # 11. Career Section
    print(analyze_career(planets))

    # 12. Marriage Section
    print(analyze_marriage(planets))

    # 13. Shadbala
    print("\n=== SHADBALA (PLANETARY STRENGTH) ===")
    print("This section evaluates the strength of planets in your chart and their ability to deliver results.\n")
    for s in improved_shadbala(planets):
        print(" ", s)

    # 14. Navamsa
    print("\n=== NAVAMSA (D9) ===")
    for p, d in planets.items():
        nav = calculate_navamsa(d.get("degree", 0), d.get("sign", ""))
        print(f"  {p:10s} → Navamsa sign: {nav}")

    # 15. Aspects (Drishti)
    print("\n=== ASPECTS (DRISHTI) ===")
    for a in calculate_aspects(planets):
        print(" ", a)

    # 16. Shastra Insights (full)
    print("\n=== SHASTRA INSIGHTS ===")
    print("The following insights are drawn from classical Vedic texts and are relevant to the planetary placements in your chart.\n")
    keywords = []
    for p, d in planets.items():
        keywords.append(p.lower())
        keywords.append(d.get("sign", "").lower())
        keywords.append(d.get("nakshatra", "").lower())

    insights = retrieve_insights(keywords)
    for i in insights:
        interpreted = interpret_text(i[:300])
        if interpreted:
            print("-", interpreted)

    # 17. Doshas
    print(detect_doshas(planets))

    # 18. Transit Analysis
    print("\n=== TRANSIT ANALYSIS ===")
    print("This section examines how current planetary transits are interacting with your natal chart and what shifts they may bring.\n")
    transit_text = saturn_transit_effect(planets)
    print(" ", transit_text)

    # 19. Sade Sati Analysis (FULL, no limit)
    print("\n🪐 TRANSIT ANALYSIS (INCLUDING SADE SATI) 🪐\n")
    print(analyze_sadesati())

    # 20. Remedies
    print(suggest_remedies(planets))

    # 21. Final Prediction
    final_pred = generate_final_prediction(planets, dasha, transit_text)
    print(final_pred)

    # 22. Overall Summary
    print("\n=== OVERALL SUMMARY ===")
    print("Your chart shows a blend of karmic challenges and growth opportunities. With the right effort and awareness, strong progress is indicated in key areas of life.")


# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    generate_report()
