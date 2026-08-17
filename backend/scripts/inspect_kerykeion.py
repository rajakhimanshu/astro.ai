import kerykeion as kr
from kerykeion import AstrologicalSubject
import os
from dotenv import load_dotenv

load_dotenv()
GEONAMES_USER = os.getenv("GEONAMES_USERNAME", "demo_user")

subject = AstrologicalSubject(
    "Test", 2006, 8, 22,
    9, 37, "Jabalpur", "IN",
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
