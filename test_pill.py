import sys
import tkinter as tk
import time
import threading

sys.path.insert(0, ".")

from src.ui.pill import StatusPill

# Create tk root
root = tk.Tk()
root.withdraw()  # hide root window

# Initialize StatusPill
pill = StatusPill(root)

def run_test():
    time.sleep(1)
    
    print(">>> Testing recording state (Yellow fluid waves + progress bar)...")
    root.after(0, lambda: pill.set_state("recording"))
    
    # Update duration over 4 seconds
    for i in range(20):
        time.sleep(0.2)
        duration = i * 0.2
        root.after(0, lambda d=duration: pill.update_duration(d))
        
    print(">>> Testing transcribing state (Spinning blue loader ring)...")
    root.after(0, lambda: pill.set_state("transcribing"))
    time.sleep(4)
    
    print(">>> Testing done state (Green smooth checkmark)...")
    root.after(0, lambda: pill.set_state("done", word_count=12))
    time.sleep(2)
    
    print(">>> Testing error state (Red smooth cross)...")
    root.after(0, lambda: pill.set_state("error"))
    time.sleep(4)
    
    print(">>> Test complete! Quitting...")
    root.after(0, root.quit)

threading.Thread(target=run_test, daemon=True).start()
root.mainloop()
