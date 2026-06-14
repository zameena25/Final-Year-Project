import tkinter as tk
from tkinter import ttk
import time
import threading

class GlowingButton:
    def __init__(self, root):
        self.root = root
        self.root.title("Glowing Button Example")
        self.root.geometry("400x300")
        self.root.configure(bg="#1e1e2e")

        # Create glowing button
        self.create_glowing_button()

    def create_glowing_button(self):
        # Main button frame for glow effect
        self.button_frame = tk.Frame(self.root, bg="#1e1e2e")
        self.button_frame.pack(pady=50)

        # The actual button
        self.button = tk.Button(
            self.button_frame,
            text="✨ Click Me ✨",
            font=("Helvetica", 16, "bold"),
            fg="white",
            bg="#7b2cbf",
            activebackground="#9d4edd",
            activeforeground="white",
            relief="flat",
            width=15,
            height=2,
            bd=0,
            highlightthickness=0,
            command=self.on_click
        )
        self.button.pack(padx=10, pady=10)

        # Start glowing animation
        self.is_glowing = True
        self.glow_thread = threading.Thread(target=self.pulse_glow, daemon=True)
        self.glow_thread.start()

        # Hover effects
        self.button.bind("<Enter>", self.on_hover)
        self.button.bind("<Leave>", self.on_leave)

    def pulse_glow(self):
        """Creates a pulsing glow effect"""
        colors = ["#7b2cbf", "#9d4edd", "#c77dff", "#e0aaff"]
        i = 0
        
        while self.is_glowing:
            try:
                color = colors[i % len(colors)]
                self.button.config(bg=color)
                self.button_frame.config(bg=color)  # Frame creates outer glow
                time.sleep(0.3)
                i += 1
            except:
                break

    def on_hover(self, e):
        self.button.config(
            bg="#c77dff",
            font=("Helvetica", 17, "bold")
        )

    def on_leave(self, e):
        pass  # Animation will handle color

    def on_click(self):
        print("🌟 Button clicked!")
        # Flash effect
        original_color = self.button["bg"]
        self.button.config(bg="#ffffff", fg="#1e1e2e")
        self.root.after(150, lambda: self.button.config(bg=original_color, fg="white"))

    def stop(self):
        self.is_glowing = False


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = GlowingButton(root)
    
    # Clean shutdown
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()