import json

# -------------------------------
# LOAD FILES
# -------------------------------
with open("kundali_rebuilt.json", "r") as f:
    kundali = json.load(f)

with open("filtered_chunks.json", "r") as f:
    chunks = json.load(f)

planets = kundali["planets"]
dasha = kundali["Vimshottari_Dasha"]
sadesati = kundali["SadeSati"]

# -------------------------------
# SMART RETRIEVAL (UPGRADED)
# -------------------------------
def retrieve_insights(keywords):
    scored = []

    for chunk in chunks:
        text = chunk["text"].lower()

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
# PLANET ANALYSIS
# -------------------------------
def analyze_planets():
    output = []

    for planet, data in planets.items():
        keywords = [
            planet.lower(),
            data["sign"].lower(),
            data["nakshatra"].lower(),
            f"house {data['house']}"
        ]

        insights = retrieve_insights(keywords)

        section = f"\n=== {planet.upper()} ===\n"
        section += f"{planet} in {data['sign']} (House {data['house']}, {data['nakshatra']})\n"

        for insight in insights:
            section += f"- {insight}\n"

        output.append(section)

    return "\n".join(output)


# -------------------------------
# MAHADASHA ANALYSIS
# -------------------------------
def analyze_dasha():
    output = "\n=== MAHADASHA ANALYSIS ===\n"

    for period in dasha[:3]:
        planet = period["planet"]

        keywords = [
            planet.lower(),
            "dasha",
            "mahadasa",
            "effects"
        ]

        insights = retrieve_insights(keywords)

        output += f"\n{planet} Mahadasha ({period['start']} - {period['end']}):\n"

        for insight in insights:
            output += f"- {insight}\n"

    return output


# -------------------------------
# SADE SATI ANALYSIS
# -------------------------------
def analyze_sadesati():
    output = "\n=== SADE SATI ANALYSIS ===\n"

    for period in sadesati:
        if period["type"] == "Sade Sati":
            keywords = [
                "saturn",
                "sade sati",
                period["rashi"].lower()
            ]

            insights = retrieve_insights(keywords)

            output += f"\n{period['phase']} Phase ({period['start']} - {period['end']}):\n"

            for insight in insights:
                output += f"- {insight}\n"

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
        output += f"- {insight}\n"

    return output


# -------------------------------
# CONJUNCTION DETECTION
# -------------------------------
def detect_conjunctions(planets):
    results = []
    planet_list = list(planets.items())

    for i in range(len(planet_list)):
        for j in range(i + 1, len(planet_list)):
            p1, d1 = planet_list[i]
            p2, d2 = planet_list[j]

            if d1["house"] == d2["house"]:
                degree_diff = abs(d1["degree"] - d2["degree"])

                results.append({
                    "planets": f"{p1} + {p2}",
                    "house": d1["house"],
                    "degree_diff": degree_diff
                })

    return results


# -------------------------------
# COMBUSTION LOGIC
# -------------------------------
def check_combustion(planets):
    results = []

    sun_degree = planets["Sun"]["degree"]

    for planet, data in planets.items():
        if planet == "Sun":
            continue

        diff = abs(sun_degree - data["degree"])

        if planet == "Mercury" and diff < 14:
            results.append(f"{planet} is combust (distance {diff:.2f}°)")

        elif planet == "Venus" and diff < 10:
            results.append(f"{planet} is combust (distance {diff:.2f}°)")

    return results


# -------------------------------
# SADE SATI REAL LOGIC
# -------------------------------
def sade_sati_analysis(planets):
    moon_sign = planets["Moon"]["sign"]

    return f"Sade Sati occurs when Saturn transits Virgo, Libra, and Scorpio relative to Moon in {moon_sign}"


# -------------------------------
# CURRENT MAHADASHA LOGIC
# -------------------------------
def current_dasha(dasha):
    for period in dasha:
        if "2026" in period["start"]:
            return f"Upcoming Mahadasha: {period['planet']} ({period['start']} - {period['end']})"

    return "Current Mahadasha not detected"


# -------------------------------
# YOGA DETECTION (RULE-BASED)
# -------------------------------
def detect_basic_yogas(planets):
    results = []

    if planets["Jupiter"]["house"] == planets["Saturn"]["house"]:
        results.append("Jupiter-Saturn conjunction: discipline + wisdom combination")

    if planets["Rahu"]["house"] == 1:
        results.append("Rahu in Lagna: strong personality, unconventional path")

    return results


# -------------------------------
# FINAL REPORT
# -------------------------------
def generate_report():
    print("\n🔱 VEDIC ASTROLOGY REPORT 🔱\n")

    print(analyze_planets())
    print(analyze_dasha())
    print(analyze_sadesati())
    print(detect_yogas())

    print("\n=== ADVANCED ANALYSIS ===\n")

    print("Conjunctions:")
    for c in detect_conjunctions(planets):
        print(c)

    print("\nCombustion:")
    for c in check_combustion(planets):
        print(c)

    print("\nSade Sati Logic:")
    print(sade_sati_analysis(planets))

    print("\nMahadasha Insight:")
    print(current_dasha(dasha))

    print("\nYoga Logic:")
    for y in detect_basic_yogas(planets):
        print(y)


# -------------------------------
# RUN
# -------------------------------
generate_report()
