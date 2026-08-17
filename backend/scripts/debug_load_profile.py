import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.user_profile_engine import load_user_profile

try:
    p = load_user_profile("john_doe")
    print("Profile loaded successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
