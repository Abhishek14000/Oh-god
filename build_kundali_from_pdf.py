"""
build_kundali_from_pdf.py
Extract structured kundali data from AstroSage PDF and generate a clean JSON.
"""

import json
import os
import re
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextBox, LTTextLine

PDF_FILE = "VedicReport10-12-20253-36-34AM (1) (1) (1) (1)_removed (1).pdf"
SMALL_PDF_FILE = "VedicReport10-12-20253-36-34AM (1) (1) (1) (1)_removed (1)_removed.pdf"
OUTPUT_FILE = "kundali_rebuilt.json"

# ─────────────────────────────────────────────
# STEP 6 – NAKSHATRA LORD MAPPING (all 27)
# ─────────────────────────────────────────────
NAKSHATRA_LORD = {
    "Ashwini": "Ketu",           "Bharani": "Venus",        "Krittika": "Sun",
    "Rohini": "Moon",            "Mrigasira": "Mars",       "Ardra": "Rahu",
    "Punarvasu": "Jupiter",      "Pushya": "Saturn",        "Ashlesha": "Mercury",
    "Magha": "Ketu",             "Purva Phalguni": "Venus", "Uttara Phalguni": "Sun",
    "Hasta": "Moon",             "Chitra": "Mars",          "Swati": "Rahu",
    "Vishakha": "Jupiter",       "Anuradha": "Saturn",      "Jyeshtha": "Mercury",
    "Mula": "Ketu",              "Purva Ashadha": "Venus",  "Uttara Ashadha": "Sun",
    "Sravana": "Moon",           "Dhanishta": "Mars",       "Shatabhisha": "Rahu",
    "Purva Bhadrapada": "Jupiter","Uttara Bhadrapada": "Saturn", "Revati": "Mercury",
}

# ─────────────────────────────────────────────
# STEP 7 – ZODIAC ORDER (for house calculation)
# ─────────────────────────────────────────────
ZODIAC_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_ALIASES = {"Scorpion": "Scorpio"}


def normalize_sign(sign):
    return SIGN_ALIASES.get(sign, sign) if sign else sign


def house_from_asc(planet_sign, asc_sign):
    asc_sign = normalize_sign(asc_sign)
    planet_sign = normalize_sign(planet_sign)
    if asc_sign in ZODIAC_ORDER and planet_sign in ZODIAC_ORDER:
        return (ZODIAC_ORDER.index(planet_sign) - ZODIAC_ORDER.index(asc_sign)) % 12 + 1
    return None


# ─────────────────────────────────────────────
# STEP 5 – DEGREE CONVERSION  27-22-36 → float
# ─────────────────────────────────────────────
def degree_to_float(deg_str):
    parts = re.split(r"-", deg_str)
    try:
        d, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return round(d + m / 60 + s / 3600, 6)
    except (IndexError, ValueError):
        return deg_str


# ─────────────────────────────────────────────
# STEP 4 – NORMALIZATION MAPS
# ─────────────────────────────────────────────
PLANET_NAME_MAP = {
    "ASC": "ASC", "Sun": "Sun", "Moon": "Moon", "Mars": "Mars",
    "Merc": "Mercury", "Jupt": "Jupiter", "Venu": "Venus",
    "Satn": "Saturn", "Rahu": "Rahu", "Ketu": "Ketu",
}

NAKSHATRA_NAME_MAP = {
    "Purvaphalgini": "Purva Phalguni",
    "Uttaraphal":    "Uttara Phalguni",
    "Uttarashadha":  "Uttara Ashadha",
    "Purvashadha":   "Purva Ashadha",
    "Satabisha":     "Shatabhisha",
}


def normalize_nakshatra(n):
    return NAKSHATRA_NAME_MAP.get(n, n)


# ─────────────────────────────────────────────
# STEP 1 – READ PDF TEXT
# ─────────────────────────────────────────────
def read_pdf(path):
    raw = extract_text(path)
    lines = raw.splitlines()
    normalized = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    return "\n".join(normalized)


# ─────────────────────────────────────────────
# STEP 2 – BASIC DETAILS
# ─────────────────────────────────────────────
def extract_basic_details(text):
    details = {}

    # Name from the very first line
    m = re.match(r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)", text)
    if m:
        details["name"] = m.group(1).strip()

    # Avkahada Chakra block – values follow "Antya\n\n..."
    # Order after Antya: DasaBalance, Lagna, LagnaLord, Rasi, RasiLord, NakshatraPada, NakshatraLord
    avk = re.search(
        r"Antya\s*\n\s*"
        r"[^\n]+\s*\n\s*"               # Dasa Balance  (e.g. "Rah  9 Y 4 M 23 D")
        r"([A-Za-z]+)\s*\n\s*"          # Lagna
        r"([A-Za-z]+)\s*\n\s*"          # Lagna Lord
        r"([A-Za-z]+)\s*\n\s*"          # Rasi
        r"([A-Za-z]+)\s*\n\s*"          # Rasi Lord
        r"([A-Za-z]+ \d)\s*\n\s*"       # Nakshatra-Pada  e.g. "Swati 2"
        r"([A-Za-z]+)",                  # Nakshatra Lord
        text,
    )
    if avk:
        details["lagna"] = avk.group(1).strip()
        details["rasi"] = avk.group(3).strip()
        nk_pada = avk.group(5).strip()
        nk_parts = nk_pada.rsplit(" ", 1)
        details["nakshatra"] = normalize_nakshatra(nk_parts[0])
        details["nakshatra_pada"] = int(nk_parts[1]) if len(nk_parts) == 2 else None
        lord_raw = avk.group(6).strip()
        lord_map = {
            "Rah": "Rahu", "Ket": "Ketu", "Sun": "Sun", "Mon": "Moon",
            "Mar": "Mars", "Mer": "Mercury", "Jup": "Jupiter",
            "Ven": "Venus", "Sat": "Saturn",
        }
        details["nakshatra_lord"] = lord_map.get(lord_raw, lord_raw)

    # Basic Details values block – they appear after the label list ends at "Bad Planets"
    bd = re.search(
        r"Bad Planets\s*\n\s*"
        r"(Male|Female)\s*\n\s*"                         # Sex
        r"(\d+\s*:\s*\d+\s*:\s*\d{4})\s*\n\s*"          # Date of Birth  "3 : 9 : 2000"
        r"(\d+\s*:\s*\d+\s*:\s*\d+)\s*\n\s*"            # Time of Birth  "0 : 0 : 18"
        r"\S[^\n]*\n\s*"                                  # Day of Birth
        r"[^\n]+\n\s*"                                    # Ishtkaal
        r"([A-Za-z][A-Za-z ]+?)\s*\n\s*"                 # Place
        r"([\d.]+)\s*\n\s*"                              # Timezone
        r"([\d\s:]+[NS])\s*\n\s*"                        # Latitude
        r"([\d\s:]+[EW])",                               # Longitude
        text,
        re.DOTALL,
    )
    if bd:
        details["date_of_birth"] = bd.group(2).replace(" ", "")
        details["time_of_birth"] = bd.group(3).replace(" ", "")
        details["place"]         = bd.group(4).strip()
        details["timezone"]      = bd.group(5).strip()
        details["latitude"]      = bd.group(6).strip()
        details["longitude"]     = bd.group(7).strip()

    return details


# ─────────────────────────────────────────────
# STEP 3 – PLANETARY POSITIONS
# ─────────────────────────────────────────────
_PLANETS_TO_KEEP = {
    "ASC", "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
}

_SIGN_NAMES = (
    "Gemini|Leo|Libra|Cancer|Taurus|Virgo|Scorpion|"
    "Sagittarius|Capricorn|Aries|Aquarius|Pisces"
)

_NAKSHATRA_NAMES = (
    "Mrigasira|Purvaphalgini|Swati|Ashlesha|Uttaraphal|Rohini|"
    "Krittika|Punarvasu|Uttarashadha|Purvashadha|Satabisha|"
    "Anuradha|Bharani|Ashwini|Ardra|Pushya|Magha|Hasta|"
    "Chitra|Vishakha|Jyeshtha|Mula|Dhanishta|Sravana"
)


_PLANETARY_SECTION_MAX_CHARS = 2000  # generous upper bound for one planet-table block


def extract_planetary_positions(text):
    sec_m = re.search(r"Planetary Positions\s*\nPlanets\s*\n", text)
    if not sec_m:
        return []
    sec_start = sec_m.start()
    sec_end_m = re.search(r"Ashtakvarga Table", text[sec_start:])
    sec = text[sec_start: sec_start + sec_end_m.start()] if sec_end_m else text[sec_start: sec_start + _PLANETARY_SECTION_MAX_CHARS]

    # --- planet names (each on its own line) ---
    raw_names = re.findall(
        r"^(ASC|Sun|Moon|Mars|Merc|Jupt|Venu|Satn|"
        r"Rahu \[R\]|Ketu \[R\]|Uran \[R\]|Nept \[R\]|Plut)$",
        sec, re.MULTILINE,
    )
    planet_norm = [
        PLANET_NAME_MAP.get(p.replace(" [R]", ""), p.replace(" [R]", ""))
        for p in raw_names
    ]

    # --- signs (between "^Sign$" and "^Latitude$") ---
    signs_m = re.search(r"^Sign$\n((?:.*\n)*?)^Latitude$", sec, re.MULTILINE)
    signs = re.findall(
        r"^(" + _SIGN_NAMES + r")$",
        signs_m.group(1) if signs_m else "",
        re.MULTILINE,
    )

    # --- degrees (dd-mm-ss on their own lines) ---
    degrees = re.findall(r"^(\d{2}-\d{2}-\d{2})$", sec, re.MULTILINE)

    # --- nakshatras (between "^Nakshatra$" and "^Pada$") ---
    nak_m = re.search(r"^Nakshatra$\n((?:.*\n)*?)^Pada$", sec, re.MULTILINE)
    nakshatras_raw = re.findall(
        r"^(" + _NAKSHATRA_NAMES + r")$",
        nak_m.group(1) if nak_m else "",
        re.MULTILINE,
    )

    # --- padas (single digits after "^Pada$") ---
    pada_m = re.search(r"^Pada$\n((?:\d\n)+)", sec, re.MULTILINE)
    pada_list = re.findall(r"^(\d)$", pada_m.group(1) if pada_m else "", re.MULTILINE)

    planets = []
    for i, norm_name in enumerate(planet_norm):
        sign     = normalize_sign(signs[i])        if i < len(signs)        else None
        deg_raw  = degrees[i]                       if i < len(degrees)      else None
        nak_raw  = nakshatras_raw[i]                if i < len(nakshatras_raw) else None
        nak      = normalize_nakshatra(nak_raw)     if nak_raw               else None
        pada     = int(pada_list[i])                if i < len(pada_list)    else None
        deg_f    = degree_to_float(deg_raw)         if deg_raw               else None
        planets.append({
            "planet": norm_name, "sign": sign,
            "degree": deg_f, "nakshatra": nak, "pada": pada,
        })

    return [p for p in planets if p["planet"] in _PLANETS_TO_KEEP]


# ─────────────────────────────────────────────
# STEP 13 – BUILD PLANETS DICT
# ─────────────────────────────────────────────
def build_planets(planet_list, asc_sign):
    result = {}
    for p in planet_list:
        name = p["planet"]
        sign = p["sign"]
        nak  = p.get("nakshatra")
        house = 1 if name == "ASC" else house_from_asc(sign, asc_sign)
        result[name] = {
            "sign": sign,
            "degree": p.get("degree"),
            "nakshatra": nak,
            "pada": p.get("pada"),
            "nakshatra_lord": NAKSHATRA_LORD.get(nak) if nak else None,
            "house": house,
        }
    return result


# ─────────────────────────────────────────────
# STEP 8 – ASHTAKAVARGA
# The raw text stores numbers column-by-column (by sign).
# Each sign group: sign_no, Sun, Moon, Mars, Merc, Jupt, Venu, Satn, Total  (9 numbers)
# ─────────────────────────────────────────────
def extract_ashtakavarga(text):
    sec = re.search(r"Ashtakvarga Table\s*\n.*?Sign No\s*\n(.*?)Chalit Table", text, re.DOTALL)
    if not sec:
        return {}

    all_nums = list(map(int, re.findall(r"\b(\d+)\b", sec.group(1))))

    planet_labels = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Total"]
    rows = {label: [] for label in planet_labels}

    i = 0
    sign_count = 0
    while i < len(all_nums) and sign_count < 12:
        if all_nums[i] == sign_count + 1 and i + 8 < len(all_nums):
            group = all_nums[i + 1: i + 9]
            for j, label in enumerate(planet_labels):
                rows[label].append(group[j])
            sign_count += 1
            i += 9
        else:
            i += 1

    return rows


# ─────────────────────────────────────────────
# STEP 9 – VIMSHOTTARI DASHA
# ─────────────────────────────────────────────
DASHA_PLANET_MAP = {
    "RAH": "Rahu", "JUP": "Jupiter", "SAT": "Saturn", "MER": "Mercury",
    "KET": "Ketu", "VEN": "Venus",   "SUN": "Sun",    "MON": "Moon", "MAR": "Mars",
}

# Standard sequence from Rahu (birth dasha for this chart)
VIMSHOTTARI_SEQUENCE = [
    "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars",
]


def _parse_2000(raw):
    """Parse 'D/ M/YY' with base 2000+yr. Returns (formatted_str, year_int)."""
    m = re.match(r"\s*(\d+)/\s*(\d+)/(\d+)\s*", str(raw))
    if not m:
        return str(raw).strip(), 0
    day, mon, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
    y = 2000 + yr
    return f"{day:02d}/{mon:02d}/{y}", y


def _set_year(date_str, new_year):
    parts = date_str.split("/")
    if len(parts) == 3:
        parts[2] = str(new_year)
    return "/".join(parts)


def extract_vimshottari(text):
    sec_m = re.search(r"Vimshottari Dasha\s*\n", text)
    if not sec_m:
        return []
    end_m = re.search(r"\n(?:Asc Lord|Navamasa Chart|Planetary Position)", text[sec_m.start():])
    block = text[sec_m.start(): sec_m.start() + end_m.start()] if end_m else text[sec_m.start():]

    maha_pat = re.compile(
        r"(RAH|JUP|SAT|MER|KET|VEN|SUN|MON|MAR)\s+-(\d+)\s+Years\s*\n\s*"
        r"([\d/\s]+?)\s*-\s*([\d/\s]+?)\s*\n"
    )

    raw = {}
    for m in maha_pat.finditer(block):
        planet = DASHA_PLANET_MAP.get(m.group(1), m.group(1))
        years  = int(m.group(2))
        start_s, sy = _parse_2000(m.group(3))
        end_s,   ey = _parse_2000(m.group(4))
        raw[planet] = {"planet": planet, "years": years,
                       "start": start_s, "end": end_s, "sy": sy, "ey": ey}

    # Walk in standard sequence and fix centuries
    ordered = [raw[p] for p in VIMSHOTTARI_SEQUENCE if p in raw]
    prev_end = 0
    for d in ordered:
        sy, ey = d["sy"], d["ey"]
        # Push start forward if it precedes previous dasha end
        if sy < prev_end - 1:
            sy += ((prev_end - 1 - sy + 99) // 100) * 100
        d["sy"] = sy
        d["start"] = _set_year(d["start"], sy)
        # Push end forward until it exceeds start
        if ey <= sy:
            ey += ((sy - ey + 100) // 100) * 100
        d["ey"] = ey
        d["end"] = _set_year(d["end"], ey)
        prev_end = ey

    return [{"planet": d["planet"], "years": d["years"],
             "start": d["start"], "end": d["end"]} for d in ordered]


# ─────────────────────────────────────────────
# STEP 10 – YOGINI DASHA
# ─────────────────────────────────────────────
YOGINI_MAP = {
    "Pi": "Pingala", "Dh": "Dhanya",   "Br": "Bhramari",
    "Ba": "Bhadrika", "Ul": "Ulka",    "Si": "Siddha",
    "Sn": "Sankata",  "Ma": "Mangala",
}


def _parse_yogini_date_raw(raw):
    """Parse Yogini date string 'D/ M/YY'. Returns (day, mon, yr, yr_base) where
    yr_base uses 1900+yr for yr>=50, else 2000+yr (century is later corrected
    by the chronological walk in extract_yogini)."""
    m = re.match(r"\s*(\d+)/\s*(\d+)/(\d+)\s*", raw)
    if not m:
        return None, None, None, None
    day, mon, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
    yr_base = 1900 + yr if yr >= 50 else 2000 + yr
    return day, mon, yr, yr_base


def extract_yogini(text):
    # Gather all Yogini Dasha occurrences across pages
    all_blocks = []
    for start_m in re.finditer(r"Yogini Dasha \|\|", text):
        end_m = re.search(r"\nhttps://www\.AstroSage", text[start_m.start():])
        chunk = text[start_m.start(): start_m.start() + end_m.start()] if end_m else text[start_m.start():]
        all_blocks.append(chunk)
    if not all_blocks:
        return []

    combined = "\n".join(all_blocks)

    # Extract all period headers: "Pi 2 Years\nFrom 29/ 9/99"
    periods = re.findall(
        r"(Pi|Dh|Br|Ba|Ul|Si|Sn|Ma)\s+(\d+)\s+Years\s*\n\s*From\s+([\d/ ]+)",
        combined,
    )

    # De-duplicate while preserving order
    seen = set()
    unique_periods = []
    for code, years, from_date in periods:
        key = (code, from_date.strip())
        if key not in seen:
            seen.add(key)
            unique_periods.append((code, int(years), from_date.strip()))

    # Parse start dates with chronological century correction
    parsed_starts = []
    prev_year = 0
    for code, years, from_date in unique_periods:
        day, mon, _, yr_base = _parse_yogini_date_raw(from_date)
        if day is None:
            parsed_starts.append(from_date.strip())
            continue
        if yr_base < prev_year:
            yr_base += ((prev_year - yr_base + 99) // 100) * 100
        prev_year = yr_base
        parsed_starts.append(f"{day:02d}/{mon:02d}/{yr_base}")

    # Build result: end[i] = start[i+1]; last entry end = start + years
    result = []
    for i, (code, years, _) in enumerate(unique_periods):
        start = parsed_starts[i]
        if i + 1 < len(parsed_starts):
            end = parsed_starts[i + 1]
        else:
            # Compute end from start year + years duration
            parts = start.split("/")
            end = f"{parts[0]}/{parts[1]}/{int(parts[2]) + years}"
        result.append({
            "yogini": YOGINI_MAP.get(code, code),
            "years": years,
            "start": start,
            "end": end,
        })

    return result


# ─────────────────────────────────────────────
# STEP 11 – SADE SATI
# ─────────────────────────────────────────────
_MONTHS = (
    "January|February|March|April|May|June|"
    "July|August|September|October|November|December"
)
MONTH_MAP = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05",     "June": "06",     "July": "07",  "August": "08",
    "September": "09","October": "10", "November": "11","December": "12",
}


def _reconstruct_dates(block):
    """Rejoin split multi-line dates."""
    # "Month Day,\nYear"
    block = re.sub(
        r"((?:" + _MONTHS + r")\s+\d+,)\s*\n\s*(\d{4})",
        r"\1 \2", block,
    )
    # "Month\nDay, Year"
    block = re.sub(
        r"((?:" + _MONTHS + r"))\s*\n\s*(\d+,\s*\d{4})",
        r"\1 \2", block,
    )
    return block


def _parse_long_date(d):
    m = re.match(r"([A-Za-z]+)\s+(\d+),\s*(\d{4})", d.strip())
    if m:
        return f"{int(m.group(2)):02d}/{MONTH_MAP.get(m.group(1), '??')}/{m.group(3)}"
    return d.strip()


def extract_sade_sati(text):
    # Collect all Sadesati Report pages
    sec_starts = [m.start() for m in re.finditer(r"\|\|\s*Sadesati Report\s*\|\|", text)]
    if not sec_starts:
        sec_starts = [m.start() for m in re.finditer(r"Sade Sati/\s*\nPanoti", text)]
    if not sec_starts:
        return []

    full_block = ""
    for start in sec_starts:
        end_m = re.search(r"https://www\.AstroSage", text[start:])
        full_block += (text[start: start + end_m.start()] if end_m else text[start:]) + "\n"

    full_block = _reconstruct_dates(full_block)

    type_rashi = re.findall(
        r"(Sade Sati|Small Panoti)\s+"
        r"(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|"
        r"Scorpio|Scorpion|Sagittarius|Capricorn|Aquarius|Pisces)",
        full_block,
    )

    date_pat = re.compile(r"(?:" + _MONTHS + r")\s+\d+,\s*\d{4}")
    all_dates = date_pat.findall(full_block)
    phases    = re.findall(r"\b(Rising|Peak|Setting)\b", full_block)

    rows = []
    for i, (t, rashi) in enumerate(type_rashi):
        start = _parse_long_date(all_dates[2 * i])     if 2 * i     < len(all_dates) else None
        end   = _parse_long_date(all_dates[2 * i + 1]) if 2 * i + 1 < len(all_dates) else None
        phase = phases[i]                               if i         < len(phases)    else None
        rows.append({
            "type": t,
            "rashi": normalize_sign(rashi),
            "start": start,
            "end": end,
            "phase": phase,
        })
    return rows


def _date_tuple(date_str):
    """Convert 'DD/MM/YYYY' to (YYYY, MM, DD) tuple for comparison/sorting."""
    parts = date_str.split("/")
    return (int(parts[2]), int(parts[1]), int(parts[0]))


def parse_sade_sati_from_small_pdf():
    raw = extract_text("VedicReport10-12-20253-36-34AM (1) (1) (1) (1)_removed (1)_removed.pdf")

    # normalize spacing
    text = re.sub(r"[ \t]+", " ", raw)

    # fix broken dates (multi-line issues)
    text = re.sub(
        r"((January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},)\s*\n\s*(\d{4})",
        r"\1 \3", text
    )
    text = re.sub(
        r"((January|February|March|April|May|June|July|August|September|October|November|December))\s*\n\s*(\d{1,2},\s*\d{4})",
        r"\1 \3", text
    )

    # extract full rows correctly
    pattern = re.compile(
        r"(Small Panoti|Sade Sati)\s+"
        r"(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)\s+"
        r"([A-Za-z]+\s+\d{1,2},\s*\d{4})\s+"
        r"([A-Za-z]+\s+\d{1,2},\s*\d{4})"
        r"(?:\s+(Rising|Peak|Setting))?"
    )

    rows = _extract_sade_sati_by_position()

    rows.sort(key=lambda x: _date_tuple(x["start"]))

    return rows


def _extract_sade_sati_by_position():
    """
    Parse the Sade Sati table by grouping pdfminer text elements
    using their x,y coordinates to reconstruct each table row.

    Column layout (approximate x positions):
      x≈ 92  – S.N.
      x≈164  – Type (e.g. "Sade Sati", "Small Panoti Taurus")
      x≈236  – Rashi (only present for "Sade Sati" rows)
      x≈308  – Start Date
      x≈380  – End Date
      x≈452  – Phase
    """
    # Collect all text elements with (page, y, x, text)
    elements = []
    for page_num, page_layout in enumerate(
        extract_pages(
            "VedicReport10-12-20253-36-34AM (1) (1) (1) (1)_removed (1)_removed.pdf"
        )
    ):
        for elem in page_layout:
            if isinstance(elem, LTTextBox):
                for line in elem:
                    if isinstance(line, LTTextLine):
                        txt = line.get_text().strip()
                        if txt:
                            elements.append(
                                (page_num, round(line.y0, 1), round(line.x0, 1), txt)
                            )

    # Identify S.N. anchors: integer text at x≈92
    sn_anchors = []
    for pg, y, x, txt in elements:
        if 80 <= x <= 155 and re.fullmatch(r"\d{1,2}", txt):
            sn_anchors.append((int(txt), pg, y))
    sn_anchors.sort(key=lambda a: a[0])

    if not sn_anchors:
        return []

    MARGIN = 3
    rows = []
    for i, (sn, pg, y_anchor) in enumerate(sn_anchors):
        y_top = y_anchor + MARGIN

        # Bottom boundary: use the next anchor ON THE SAME PAGE; otherwise page bottom
        y_bot = -9999
        for j in range(i + 1, len(sn_anchors)):
            next_sn, next_pg, next_y = sn_anchors[j]
            if next_pg == pg:
                y_bot = next_y      # strict lower bound (y > y_bot)
                break

        # Collect all elements on this page within this row's y range
        # Use strict lower bound to avoid including elements that belong to the next row
        row_elems = [
            (y, x, txt)
            for p, y, x, txt in elements
            if p == pg and y_bot < y <= y_top
        ]
        row_elems.sort(key=lambda e: (-e[0], e[1]))

        # Separate into columns by x threshold
        type_parts, rashi_parts, start_parts, end_parts, phase_parts = [], [], [], [], []
        for y, x, txt in row_elems:
            if x < 80:
                pass  # outside table (e.g. page footer at x≈10) — skip
            elif x <= 155:
                pass  # S.N. — skip
            elif x <= 220:
                # Type column – skip non-table noise such as URL footer lines
                if re.search(r"https?://|AstroSage|Printing Date", txt):
                    continue
                type_parts.append(txt)
            elif x <= 295:
                rashi_parts.append(txt)
            elif x <= 370:
                start_parts.append(txt)
            elif x <= 445:
                # End date column – may contain an embedded phase (e.g. "June 22, 2044 Setting")
                phase_match = re.search(r"(Rising|Peak|Setting)", txt)
                if phase_match:
                    phase_parts.append(phase_match.group(1))
                end_parts.append(txt)
            else:
                # Phase column – sometimes end date fragment bleeds here
                # e.g. "June 22, 2044 Setting" or "May 02, 2098 Rising"
                m = re.search(
                    r"([A-Za-z]+\s+\d{1,2},\s*\d{4})\s+(Rising|Peak|Setting)", txt
                )
                if m:
                    end_parts.append(m.group(1))
                    phase_parts.append(m.group(2))
                elif re.search(r"Rising|Peak|Setting", txt):
                    phase_parts.append(txt.strip())
                else:
                    end_parts.append(txt)

        # Reconstruct full type string
        type_str = " ".join(type_parts).strip()

        m_type = re.match(r"(Small Panoti|Sade Sati)\s*(.*)", type_str)
        if not m_type:
            continue
        base_type = m_type.group(1)
        inline_rashi = m_type.group(2).strip()

        if inline_rashi:
            rashi = normalize_sign(inline_rashi)
        elif rashi_parts:
            rashi = normalize_sign(" ".join(rashi_parts).strip())
        else:
            continue

        if rashi not in ZODIAC_ORDER:
            continue

        _DATE_PAT = (
            r"(January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{1,2},\s*\d{4}"
        )

        # Combine start and end columns so partial dates split across columns are joined
        combined = re.sub(r"\s+", " ", " ".join(start_parts + end_parts)).strip()
        date_matches = list(re.finditer(_DATE_PAT, combined))

        start_str = date_matches[0].group(0) if len(date_matches) >= 1 else None
        end_str = date_matches[1].group(0) if len(date_matches) >= 2 else None

        if not start_str or not end_str:
            continue

        start_fmt = _parse_long_date(start_str)
        end_fmt = _parse_long_date(end_str)

        try:
            if _date_tuple(start_fmt) >= _date_tuple(end_fmt):
                continue
        except Exception:
            continue

        phase = " ".join(phase_parts).strip() or None

        rows.append({
            "type":  base_type,
            "rashi": rashi,
            "start": start_fmt,
            "end":   end_fmt,
            "phase": phase,
        })

    return rows


# ─────────────────────────────────────────────
# STEP 12 – KALSARPA
# ─────────────────────────────────────────────
def extract_kalsarpa(text):
    if re.search(r"free from Kalsarpa Yoga", text, re.IGNORECASE):
        return False
    if re.search(r"Kalsarpa Yoga", text, re.IGNORECASE):
        return True
    return None


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("Starting kundali extraction...")

    if not os.path.exists(PDF_FILE):
        raise FileNotFoundError(f"{PDF_FILE} not found")
    if not os.path.exists(SMALL_PDF_FILE):
        raise FileNotFoundError(f"{SMALL_PDF_FILE} not found")

    text = read_pdf(PDF_FILE)                          # STEP 1
    basic        = extract_basic_details(text)         # STEP 2
    print("Basic details extracted")
    planet_list  = extract_planetary_positions(text)   # STEP 3 & 4
    asc_sign     = basic.get("lagna", "Gemini")        # STEP 7
    planets      = build_planets(planet_list, asc_sign)# STEP 13
    print("Planets extracted")
    ashtakavarga = extract_ashtakavarga(text)          # STEP 8
    print("Ashtakavarga extracted")
    vimshottari  = extract_vimshottari(text)           # STEP 9
    print("Vimshottari extracted")
    yogini       = extract_yogini(text)                # STEP 10
    print("Yogini extracted")
    sade_sati    = parse_sade_sati_from_small_pdf()    # STEP 11 (new)
    print("Sade Sati extracted")
    kalsarpa     = extract_kalsarpa(text)              # STEP 12

    output = {                                         # STEP 14
        "basic_details":    basic,
        "planets":          planets,
        "Ashtakavarga":     ashtakavarga,
        "Vimshottari_Dasha":vimshottari,
        "Yogini_Dasha":     yogini,
        "SadeSati":         sade_sati,
        "Kalsarpa":         kalsarpa,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:   # STEP 15
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("kundali_rebuilt.json successfully created")


if __name__ == "__main__":
    main()
