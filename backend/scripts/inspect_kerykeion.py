import kerykeion as kr
from kerykeion import AstrologicalSubject
import os
from dotenv import load_dotenv

load_dotenv()
GEONAMES_USER = os.getenv("GEONAMES_USERNAME") or None

subject = AstrologicalSubject(
    "Test", 1990, 1, 1,
    12, 0, "New York", "US",
    geonames_username=GEONAMES_USER,
    zodiac_type='Sidereal',
    sidereal_mode='LAHIRI',
    houses_system_identifier='W'
)

print("Methods in AstrologicalSubject:")
print([m for m in dir(subject) if not m.startswith('_')])

model = subject.model()
print("\nMethods in SubjectModel:")
print([m for m in dir(model) if not m.startswith('_')])
