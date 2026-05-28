"""
Test: launch splash, then settings, then quit.
"""
import sys
import threading
import time

sys.path.insert(0, ".")

from src.main import VoiceFlowApp

app = VoiceFlowApp()

def test_flow():
    time.sleep(2)
    print("Opening settings...")
    app._root.after(0, lambda: app._open_settings(highlight_api_key=False))
    time.sleep(5)
    print("Quitting test...")
    app._root.after(0, app._quit)

threading.Thread(target=test_flow, daemon=True).start()
app.run()
