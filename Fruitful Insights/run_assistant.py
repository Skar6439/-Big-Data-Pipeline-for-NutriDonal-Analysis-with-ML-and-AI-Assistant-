#!/usr/bin/env python
"""
Fruit Nutrition AI Assistant
Run this from the project root: python run_assistant.py
"""

import sys
import os

# Add src to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Now we can import from src
from ai_assistant import interactive_chat

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FRUIT NUTRITION AI ASSISTANT")
    print("=" * 60)
    print("Type 'exit' or 'quit' to end the session.")
    print("=" * 60)
    interactive_chat()