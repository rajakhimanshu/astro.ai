import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.agent import ask

try:
    print("Testing chat with user profile...")
    response = ask("Tell me about my career", user_id="john_doe")
    print("\nRESPONSE:")
    print(response)
except Exception as e:
    import traceback
    traceback.print_exc()
