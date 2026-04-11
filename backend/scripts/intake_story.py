import ollama
import json
from core.memory import add_event

def extract_events_from_text(story_text):
    """Uses LLM to extract structured life events from free text."""
    prompt = f"""
    Analyze the following life story and extract a list of specific, dated events.
    Return ONLY a JSON array of objects. No intro, no conclusion.

    Schema for each object:
    {{
      "date": "YYYY-MM-DD",
      "title": "Short descriptive title",
      "description": "1-2 sentence detail",
      "domain": "career, relationship, health, family, finance, spiritual, or education",
      "emotion_score": integer from -5 to 5,
      "outcome": "the result"
    }}

    STORY:
    {story_text}

    JSON ARRAY:
    """

    response = ollama.chat(
        model='mistral',
        messages=[{'role': 'user', 'content': prompt}]
    )

    content = response['message']['content'].strip()
    # Remove markdown formatting if present
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        events = json.loads(content)
        # Ensure it's a list and filter out non-dict items
        if isinstance(events, list):
            return [ev for ev in events if isinstance(ev, dict)]
        return []
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return []

def run_intake():
    print("--- JYOTISH AI: LIFE STORY INTAKE ---")
    print("Tip: If your story is very long, paste it in sections (e.g., Education, then Career).")
    print("Paste your story below (press Enter twice to finish):")

    
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    
    story_text = "\n".join(lines).strip()
    if not story_text:
        print("Empty story. Exiting.")
        return

    print("\nExtracting events using Mistral...")
    events = extract_events_from_text(story_text)
    
    if not events:
        print("No events could be extracted.")
        return

    print(f"\nExtracted {len(events)} events. Storing in database...")
    for ev in events:
        try:
            print(f"- Storing: {ev['title']} ({ev['date']})...")
            add_event(
                date=ev['date'],
                title=ev['title'],
                description=ev['description'],
                domain=ev['domain'],
                emotion_score=ev['emotion_score'],
                outcome=ev['outcome']
            )
        except Exception as e:
            print(f"  Error storing event '{ev['title']}': {e}")

    print("\nDONE! All events processed.")

if __name__ == '__main__':
    run_intake()
