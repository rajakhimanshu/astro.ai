from core.memory import add_event, init_database

# Initialize the database first
init_database()

# ADD YOUR LIFE EVENTS BELOW
# Format: add_event(
#   date='YYYY-MM-DD',
#   title='Short title of event',
#   description='Full description in your own words',
#   domain='career' or 'relationship' or 'health' or 'family' or 'finance' or 'spiritual',
#   emotion_score=-5 to +5 (negative=bad, positive=good, 0=neutral),
#   outcome='What happened as a result'
# )

# EXAMPLE EVENTS — Replace with your own real events
add_event(
    date='2021-03-15',
    title='Lost my first job',
    description='Got laid off from my first job due to company downsizing. It was completely unexpected and I felt lost for months.',
    domain='career',
    emotion_score=-4,
    outcome='Took 6 months to find a new job. Used the time to learn new skills.'
)

add_event(
    date='2022-08-01',
    title='Started new relationship',
    description='Met someone and started dating. Felt very hopeful and happy.',
    domain='relationship',
    emotion_score=4,
    outcome='Relationship lasted 8 months. Ended mutually.'
)

print('All events added successfully!')
