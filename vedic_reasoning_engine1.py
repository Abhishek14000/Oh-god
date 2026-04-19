import json

# Load data
with open("kundali_rebuilt.json", "r") as f:
    kundali = json.load(f)

with open("filtered_chunks.json", "r") as f:
    chunks = json.load(f)

planets = kundali["planets"]
dasha = kundali["Vimshottari_Dasha"]
sadesati = kundali["SadeSati"]

# -------------------------------
# Helper: find relevant chunks
# -------------------------------
def retrieve_insights(keywords):
    results = []

    for chunk in chunks:
        text = chunk["text"].lower()

        if any(k in text for k in keywords):
            results.append(chunk["text"])

    return results[:5]  # top 5 only


# -------------------------------
# Planet Analysis
# -------------------------------
def analyze_planets():
    output = []

    for planet, data in planets.items():
        keywords = [
            planet.lower(),
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
