from core.astro_engine import calculate_all_dignities

def calculate_chara_karakas(planets):
    """
    Calculates the 7 Chara Karakas (Jaimini system) based on planetary degrees.
    The planet with highest degree is Atmakaraka, next is Amatyakaraka, etc.
    Excludes Rahu and Ketu in the standard 7-karaka system.
    """
    # Sort planets by degree within sign (descending)
    target_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    # Create list of (planet_name, degree)
    planet_degrees = []
    for name in target_planets:
        if name in planets:
            planet_degrees.append((name, planets[name]['degree']))
            
    # Sort by degree descending
    sorted_planets = sorted(planet_degrees, key=lambda x: x[1], reverse=True)
    
    labels = [
        "Atmakaraka (Soul)",
        "Amatyakaraka (Career/Minister)",
        "Bhratrikaraka (Siblings/Courage)",
        "Matrikaraka (Mother/Education)",
        "Putrakaraka (Children/Intelligence)",
        "Gnatikaraka (Relatives/Enemies)",
        "Darakaraka (Spouse/Partners)"
    ]
    
    karakas = []
    for i in range(min(len(sorted_planets), len(labels))):
        name, deg = sorted_planets[i]
        karakas.append({
            "label": labels[i],
            "planet": name,
            "degree": deg
        })
        
    return karakas

def get_sthira_karakas():
    """Returns fixed (Sthira) significators."""
    return [
        {"label": "Atmakaraka (Fixed)", "planet": "Sun"},
        {"label": "Amatyakaraka (Fixed)", "planet": "Mercury"},
        {"label": "Bhratrikaraka (Fixed)", "planet": "Mars"},
        {"label": "Matrikaraka (Fixed)", "planet": "Moon"},
        {"label": "Putrakaraka (Fixed)", "planet": "Jupiter"},
        {"label": "Gnatikaraka (Fixed)", "planet": "Saturn"},
        {"label": "Darakaraka (Fixed)", "planet": "Venus"}
    ]
