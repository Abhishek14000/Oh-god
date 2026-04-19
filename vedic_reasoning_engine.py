import json
import re

# ---------------- LOAD DATA ----------------

with open("kundali_rebuilt.json", "r", encoding="utf-8") as f:
    kundali = json.load(f)

with open("all_books_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# ---------------- HELPERS ----------------

def normalize(text):
    return text.lower()

def score_chunk(chunk_text, planet, sign, house, nakshatra):
    text = normalize(chunk_text)
    score = 0

    # Strong contextual matches
    if planet.lower() in text and str(house) in text:
        score += 8

    if planet.lower() in text and sign.lower() in text:
        score += 6

    # Individual matches
    if planet.lower() in text:
        score += 3

    if sign.lower() in text:
        score += 2

    if nakshatra.lower() in text:
        score += 2

    return score


# ---------------- CONJUNCTION DETECTION ----------------

def detect_conjunctions(planets):
    conjunctions = []

    planet_list = list(planets.items())

    for i in range(len(planet_list)):
        for j in range(i+1, len(planet_list)):
            p1, d1 = planet_list[i]
            p2, d2 = planet_list[j]

            if d1["sign"] == d2["sign"]:
                diff = abs(d1["degree"] - d2["degree"])

                if diff <= 8:
                    strength = "strong" if diff <= 5 else "moderate"

                    conjunctions.append({
                        "planets": (p1, p2),
                        "sign": d1["sign"],
                        "degree_diff": round(diff, 2),
                        "strength": strength
                    })

    return conjunctions


# ---------------- COMBUSTION ----------------

def detect_combustion(planets):
    combustion = []

    sun_deg = planets["Sun"]["degree"]
    sun_sign = planets["Sun"]["sign"]

    for planet, data in planets.items():
        if planet == "Sun":
            continue

        if data["sign"] == sun_sign:
            diff = abs(data["degree"] - sun_deg)

            if planet == "Mercury" and diff < 14:
                combustion.append({
                    "planet": planet,
                    "degree_diff": round(diff, 2),
                    "type": "mild combustion" if diff > 6 else "strong combustion"
                })

            elif diff < 10:
                combustion.append({
                    "planet": planet,
                    "degree_diff": round(diff, 2),
                    "type": "combust"
                })

    return combustion


# ---------------- RETRIEVAL ENGINE ----------------

def retrieve_insights(planet, data):
    results = []

    for chunk in chunks:
        text = chunk.get("text", "")

        # filter garbage / short text
        if len(text) < 50:
            continue

        score = score_chunk(
            text,
            planet,
            data["sign"],
            data["house"],
            data["nakshatra"]
        )

        if score > 6:
            results.append((score, text))

    results.sort(reverse=True, key=lambda x: x[0])

    return results[:5]


# ---------------- MAIN ENGINE ----------------

def run_engine():
    planets = kundali["planets"]

    print("\n==============================")
    print(" PLANETARY INSIGHTS ")
    print("==============================\n")

    for planet, data in planets.items():
        print(f"\n--- {planet} ({data['sign']} | House {data['house']}) ---")

        insights = retrieve_insights(planet, data)

        if not insights:
            print("No strong matches found.\n")
            continue

        for score, text in insights:
            print(f"[Score: {score}] {text[:200]}...\n")


    print("\n==============================")
    print(" CONJUNCTIONS ")
    print("==============================\n")

    conjunctions = detect_conjunctions(planets)

    for conj in conjunctions:
        print(conj)


    print("\n==============================")
    print(" COMBUSTION ")
    print("==============================\n")

    combustion = detect_combustion(planets)

    for c in combustion:
        print(c)


if __name__ == "__main__":
    run_engine()
