import json
import re

# ---------------- LOAD DATA ----------------

with open("kundali_rebuilt.json", "r", encoding="utf-8") as f:
    kundali = json.load(f)

with open("all_books_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# ---------------- CONSTANTS ----------------

MODERN_WORDS = {
    "screen", "smartphone", "internet", "technology", "social media",
    "burnout", "anxiety", "depression", "stress", "app", "digital",
    "online", "website", "computer", "phone", "email", "therapy",
    "mindfulness", "self-care", "productivity hack", "career advice",
}

ASTROLOGICAL_TERMS = {
    "house", "sign", "nakshatra", "planet", "conjunction", "aspect",
    "yoga", "rasi", "lagna", "ascendant", "lord", "bhava", "dasha",
    "transit", "retrograde", "exalted", "debilitated", "combustion",
    "trine", "kendra", "trikona", "dispositor", "vargottama",
    "moolatrikona", "graha", "jyotish", "vedic", "aries", "taurus",
    "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
    "sun", "moon", "mercury", "venus", "mars", "jupiter",
    "saturn", "rahu", "ketu",
}

HOUSE_THEMES = {
    1: "self, body, and personality",
    2: "wealth, speech, and family",
    3: "courage, siblings, and communication",
    4: "home, mother, and inner peace",
    5: "intelligence, progeny, and past merit",
    6: "enemies, disease, and service",
    7: "partnership, spouse, and trade",
    8: "longevity, transformation, and hidden matters",
    9: "dharma, fortune, and the guru",
    10: "karma, vocation, and public life",
    11: "gains, aspirations, and elder siblings",
    12: "liberation, foreign lands, and expenditure",
}

MIN_CHUNK_LENGTH = 50          # minimum characters for a chunk to be scored
MIN_YOGA_CHUNK_LENGTH = 80     # minimum characters for yoga pattern matching
YOGA_TEXT_PREVIEW_LENGTH = 200  # characters to preview per yoga match

CONJUNCTION_EFFECTS = {
    frozenset({"Sun", "Mercury"}): (
        "Forms Budh Aditya Yoga — solar intelligence merged with eloquence grants "
        "authority of speech and administrative acumen."
    ),
    frozenset({"Sun", "Moon"}): (
        "Amavasya conjunction — the mind and soul share the same light; "
        "introspection and intensity of purpose."
    ),
    frozenset({"Sun", "Mars"}): (
        "Solar energy intensifies Martian drive — courageous and authoritative, "
        "prone to rashness if unrestrained."
    ),
    frozenset({"Sun", "Venus"}): (
        "Artistic sensibility meets solar authority — creative ambition; "
        "Venus may be overpowered near the Sun."
    ),
    frozenset({"Sun", "Jupiter"}): (
        "Guru and Sun together — wisdom enhanced by dignity; philosophical leadership."
    ),
    frozenset({"Sun", "Saturn"}): (
        "Tension between the king and the servant — discipline through struggle; "
        "notable karmic weight."
    ),
    frozenset({"Moon", "Mercury"}): (
        "Emotional intelligence and analytic mind — strong memory and linguistic gifts."
    ),
    frozenset({"Moon", "Mars"}): (
        "Emotional intensity and impulsive action — Chandra Mangala Yoga; "
        "possible wealth through enterprise."
    ),
    frozenset({"Moon", "Jupiter"}): (
        "Gaja Kesari potential — wisdom and popularity if in kendra; mental beneficence."
    ),
    frozenset({"Moon", "Venus"}): (
        "Aesthetic sensitivity and emotional warmth — refined tastes, fond of pleasure."
    ),
    frozenset({"Moon", "Saturn"}): (
        "Emotional contraction and discipline — Vish Yoga possible; patience born of suffering."
    ),
    frozenset({"Mars", "Mercury"}): (
        "Sharp and combative intellect — technical skill; Mercury may lose calm judgment."
    ),
    frozenset({"Mars", "Jupiter"}): (
        "Dharma and courage united — righteous action; Guru Mangala Yoga enhances ambition."
    ),
    frozenset({"Mars", "Venus"}): (
        "Passion and artistry combined — strong desires; relationships may be intense."
    ),
    frozenset({"Mars", "Saturn"}): (
        "Force and restraint in conflict — tremendous endurance; potential for disciplined enterprise."
    ),
    frozenset({"Jupiter", "Saturn"}): (
        "The great teacher meets the great taskmaster — wisdom through hardship; "
        "spiritual depth over time."
    ),
    frozenset({"Jupiter", "Venus"}): (
        "Expansion of pleasure and wisdom — creative abundance; possible indulgence."
    ),
    frozenset({"Jupiter", "Mercury"}): (
        "Philosophy and eloquence united — scholarly capacity, gift of teaching."
    ),
    frozenset({"Venus", "Saturn"}): (
        "Artistic discipline — beauty through effort; longevity in relationships."
    ),
    frozenset({"Venus", "Mercury"}): (
        "Refined communication and aesthetic sensibility — literary or artistic talent."
    ),
    frozenset({"Saturn", "Mercury"}): (
        "Methodical and precise intellect — technical mastery; gravity and weight in speech."
    ),
}

# ---------------- HELPERS ----------------

def _ordinal(n):
    suffixes = {1: "1st", 2: "2nd", 3: "3rd"}
    return suffixes.get(n, f"{n}th")


def _house_theme(house):
    return HOUSE_THEMES.get(house, "this domain of life")


def _is_classical_sentence(sentence):
    """Return True if the sentence is astrologically meaningful and classical."""
    words = sentence.split()
    if len(words) < 6:
        return False
    sentence_lower = sentence.lower()
    for modern in MODERN_WORDS:
        if modern in sentence_lower:
            return False
    return any(term in sentence_lower for term in ASTROLOGICAL_TERMS)


def _conjunction_interpretation(p1, p2):
    key = frozenset({p1, p2})
    return CONJUNCTION_EFFECTS.get(
        key,
        f"Combined influence of {p1} and {p2} — blended planetary natures "
        f"shape the native's expression of both significations.",
    )


def _combustion_interpretation(planet, combustion_data):
    diff = combustion_data["degree_diff"]
    ctype = combustion_data["type"]
    if planet == "Mercury":
        if ctype == "budh_aditya":
            return (
                f"Mercury within {diff}° of the Sun forms Budh Aditya Yoga — "
                f"solar radiance empowers Mercury's intelligence, granting sharp intellect, "
                f"eloquence, and authority aligned with the Sun. Not purely detrimental — "
                f"wisdom here is solar in quality."
            )
        return (
            f"Mercury at {diff}° from the Sun — mild combustion reduces independent "
            f"judgment; speech and reasoning become aligned with solar (ego/authority) "
            f"themes rather than neutral analysis."
        )
    return (
        f"{planet} is combust ({diff}° from the Sun) — planetary significations of "
        f"{planet} are subsumed into solar themes; the native's expression of "
        f"{planet.lower()}-related matters may be diminished or redirected through "
        f"solar authority."
    )


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
                # Within 12°: Budh Aditya Yoga (solar intelligence, not purely negative)
                ctype = "budh_aditya" if diff <= 12 else "mild combustion"
                combustion.append({
                    "planet": planet,
                    "degree_diff": round(diff, 2),
                    "type": ctype
                })

            elif diff < 10:
                combustion.append({
                    "planet": planet,
                    "degree_diff": round(diff, 2),
                    "type": "combust"
                })

    return combustion


# ---------------- YOGA DETECTION (FROM SHASTRA) ----------------

INTERPRETIVE_WORDS = {
    "combination", "when", "if", "gives", "results", "indicates",
    "produces", "yoga", "conjunction", "together", "conjoined",
    "aspected", "associated", "placed",
}


def detect_yogas_from_chunks(conjunctions):
    print("\n==============================")
    print(" YOGA DETECTION (FROM SHASTRA) ")
    print("==============================\n")

    for conj in conjunctions:
        p1, p2 = conj["planets"]
        matches = []

        for chunk in chunks:
            text = chunk.get("text", "").lower()

            if len(text) < MIN_YOGA_CHUNK_LENGTH:
                continue

            if p1.lower() not in text or p2.lower() not in text:
                continue

            # Score by presence of interpretive / action language
            score = sum(1 for word in INTERPRETIVE_WORDS if word in text)
            if score >= 2:
                matches.append((score, text))

        # Rank by relevance before printing
        matches.sort(reverse=True, key=lambda x: x[0])

        count = 0
        for score, text in matches:
            if count >= 10:
                break

            print(f"Possible yoga involving {p1} and {p2}:")
            print(text[:YOGA_TEXT_PREVIEW_LENGTH] + "...\n")

            count += 1


# ---------------- RETRIEVAL ENGINE ----------------

def retrieve_insights(planet, data):
    results = []

    for chunk in chunks:
        text = chunk.get("text", "")

        # filter garbage / short text
        if len(text) < MIN_CHUNK_LENGTH:
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


# ---------------- SYNTHESIS ----------------

def synthesize_insight(insights):
    combined = []

    for score, text in insights:
        sentences = re.split(r'[.?!]', text)

        for s in sentences:
            s = s.strip()
            if _is_classical_sentence(s):
                combined.append(s)

    # dict.fromkeys preserves insertion order while removing duplicates,
    # keeping the highest-scoring sentences first
    unique = list(dict.fromkeys(combined))

    return unique[:5]


# ---------------- CONTEXTUAL SYNTHESIS ----------------

def interpret_planet(planet, data, insights):
    """Generate 3–5 refined classical interpretations for a planet."""
    sign = data["sign"]
    house = data["house"]
    nakshatra = data["nakshatra"]

    preamble = (
        f"{planet} situated in {sign}, occupying the {_ordinal(house)} bhava, "
        f"under the asterism of {nakshatra}"
    )

    sentences = synthesize_insight(insights)
    interpretations = [preamble] + sentences[:4]
    return interpretations


# ---------------- CROSS-PLANET ANALYSIS ----------------

def holistic_analysis(planets):
    print("\n==============================")
    print(" CROSS-PLANET ANALYSIS ")
    print("==============================\n")

    sign_groups = {}
    house_groups = {}

    for planet, data in planets.items():
        sign_groups.setdefault(data["sign"], []).append(planet)
        house_groups.setdefault(data["house"], []).append(planet)

    # Stelliums: 3+ planets in the same sign
    for sign, planet_list in sign_groups.items():
        if len(planet_list) >= 3:
            print(
                f"Stellium in {sign}: {', '.join(planet_list)} — "
                f"concentrated planetary energy intensifies the themes of this sign and its corresponding bhava."
            )

    # House clustering: 2+ planets in the same house
    for house, planet_list in house_groups.items():
        if len(planet_list) >= 2:
            print(
                f"House {house} clustering: {', '.join(planet_list)} — "
                f"multiple grahas amplify {_house_theme(house)}."
            )

    # Notable cross-planet combinations
    saturn = planets.get("Saturn")
    jupiter = planets.get("Jupiter")

    if saturn and jupiter and saturn["house"] == jupiter["house"]:
        house = saturn["house"]
        print(
            f"\nSaturn + Jupiter conjunct in House {house}: "
            f"Tension between expansion and restriction yields spiritual discipline; "
            f"wisdom is earned through perseverance."
        )

    if saturn and saturn["house"] == 12:
        print(
            f"\nSaturn in the 12th house: Classical indicator of spiritual discipline, "
            f"hidden strength, and eventual liberation (moksha). "
            f"Foreign residence or institutionalized service is possible."
        )

    print()


# ---------------- MAIN ENGINE ----------------

def run_engine():
    planets = kundali["planets"]

    conjunctions = detect_conjunctions(planets)
    combustion = detect_combustion(planets)

    # Build per-planet lookup maps
    conjunction_map = {}
    for conj in conjunctions:
        p1, p2 = conj["planets"]
        conjunction_map.setdefault(p1, []).append(conj)
        conjunction_map.setdefault(p2, []).append(conj)

    combustion_map = {c["planet"]: c for c in combustion}

    # Per-planet structured output
    for planet, data in planets.items():
        print(f"\n{'=' * 30}")
        print(f" PLANET: {planet.upper()}")
        print(f"{'=' * 30}\n")

        insights = retrieve_insights(planet, data)
        interpretations = interpret_planet(planet, data, insights)

        print("• Classical Interpretation:")
        for line in interpretations:
            print(f"  - {line}")

        # Conjunction influence
        planet_conjs = conjunction_map.get(planet, [])
        if planet_conjs:
            print("\n• Conjunction Influence:")
            for conj in planet_conjs:
                p1, p2 = conj["planets"]
                other = p1 if p2 == planet else p2
                interp = _conjunction_interpretation(planet, other)
                print(
                    f"  - {planet} conjoins {other} in {conj['sign']} "
                    f"({conj['strength']}, {conj['degree_diff']}°): {interp}"
                )

        # Combustion effect
        if planet in combustion_map:
            print("\n• Combustion Effect:")
            print(f"  - {_combustion_interpretation(planet, combustion_map[planet])}")

        print()

    holistic_analysis(planets)

    detect_yogas_from_chunks(conjunctions)


if __name__ == "__main__":
    run_engine()
