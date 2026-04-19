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
# FINAL REPORT
# -------------------------------
def generate_report():
    print("\n🔱 VEDIC ASTROLOGY REPORT 🔱\n")

    print(analyze_planets())
    print(analyze_dasha())
    print(analyze_sadesati())
    print(detect_yogas())


# -------------------------------
# RUN
# -------------------------------
generate_report()            planet.lower(),
            data["sign"].lower(),
            data["nakshatra"].lower(),
            str(data["house"])
        ]

        insights = retrieve_insights(keywords)

        section = f"\n=== {planet.upper()} ===\n"
        section += f"{planet} in {data['sign']} (House {data['house']}, {data['nakshatra']})\n"

        for i, insight in enumerate(insights):
            section += f"- {insight}\n"

        output.append(section)

    return "\n".join(output)


# -------------------------------
# Mahadasha Analysis
# -------------------------------
def analyze_dasha():
    output = "\n=== MAHADASHA ANALYSIS ===\n"

    for period in dasha[:3]:  # focus on important periods
        planet = period["planet"]

        keywords = [planet.lower(), "dasha", "mahadasa"]
        insights = retrieve_insights(keywords)

        output += f"\n{planet} Mahadasha ({period['start']} - {period['end']}):\n"

        for i, insight in enumerate(insights):
            output += f"- {insight}\n"

    return output


# -------------------------------
# Sade Sati Analysis
# -------------------------------
def analyze_sadesati():
    output = "\n=== SADE SATI ANALYSIS ===\n"

    for period in sadesati:
        if period["type"] == "Sade Sati":
            keywords = ["saturn", "sade sati", period["rashi"].lower()]
            insights = retrieve_insights(keywords)

            output += f"\n{period['phase']} Phase ({period['start']} - {period['end']}):\n"

            for insight in insights:
                output += f"- {insight}\n"

    return output


# -------------------------------
# Yoga Detection (basic)
# -------------------------------
def detect_yogas():
    output = "\n=== YOGA INDICATIONS ===\n"

    keywords = ["yoga", "raj yoga", "dhan yoga", "vipreet"]
    insights = retrieve_insights(keywords)

    for insight in insights:
        output += f"- {insight}\n"

    return output


# -------------------------------
# Final Report
# -------------------------------
def generate_report():
    print("\n🔱 VEDIC ASTROLOGY REPORT 🔱\n")

    print(analyze_planets())
    print(analyze_dasha())
    print(analyze_sadesati())
    print(detect_yogas())


# Run
generate_report()
