import ollama
import json
import os
from core.memory import add_event, init_database

# Path to your story file
STORY_FILE = 'data/my_story.txt'

def extract_events_from_story(story_text):
    prompt = f'''
    Read this person's life story and extract all significant life events.
    For each event, output a JSON array with objects containing:
    date (YYYY-MM-DD, estimate if not exact),
    title (short 5 word max),
    description (full detail),
    domain (career/relationship/health/family/finance/spiritual),
    emotion_score (-5 to 5),
    outcome (what resulted)
    
    Story: {story_text}
    
    Output ONLY valid JSON array, nothing else.
    '''
    response = ollama.chat(model='mistral', messages=[
        {'role': 'user', 'content': prompt}
    ])
    
    content = response['message']['content']
    try:
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        json_str = content[start_idx:end_idx]
        events = json.loads(json_str)
        return events
    except Exception as e:
        print(f"Error parsing JSON from AI: {e}")
        print(f"Full response: {content}")
        return []

def main():
    if not os.path.exists(STORY_FILE):
        print(f"❌ Error: {STORY_FILE} not found. Please create it first.")
        return

    with open(STORY_FILE, 'r', encoding='utf-8') as f:
        my_story = f.read()

    print(f'-> Reading story from {STORY_FILE}...')
    events = extract_events_from_story(my_story)
    
    if events:
        init_database()
        print(f'-> Found {len(events)} events. Saving to memory...')
        for event in events:
            add_event(**event)
        print(f'✅ Successfully extracted and saved {len(events)} events!')
    else:
        print("❌ No events found in the story.")

if __name__ == "__main__":
    main()
