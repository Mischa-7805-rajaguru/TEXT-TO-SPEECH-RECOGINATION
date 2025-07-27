import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import cv2
import pytesseract
import pyttsx3
from PIL import Image, ImageTk
import threading
import numpy as np

class OCRTextToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Text-to-Speech Application")
        self.root.geometry("800x600")
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self.is_speaking = False
        
        # Configure TTS engine
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.8)  # Volume level
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="OCR Text-to-Speech Application", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Load image button
        self.load_button = tk.Button(button_frame, text="Load Image", 
                                   command=self.load_image, bg="lightblue")
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Extract text button
        self.extract_button = tk.Button(button_frame, text="Extract Text (OCR)", 
                                      command=self.extract_text, bg="lightgreen",
                                      state=tk.DISABLED)
        self.extract_button.pack(side=tk.LEFT, padx=5)
        
        # Play button
        self.play_button = tk.Button(button_frame, text="▶ Play", 
                                   command=self.play_text, bg="orange",
                                   state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_button = tk.Button(button_frame, text="⏹ Stop", 
                                   command=self.stop_speech, bg="red",
                                   state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        self.clear_button = tk.Button(button_frame, text="Clear", 
                                    command=self.clear_text, bg="lightgray")
        self.clear_button.pack(side=tk.RIGHT)
        
        # Content frame
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Image frame
        image_frame = tk.LabelFrame(content_frame, text="Loaded Image", font=("Arial", 10, "bold"))
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.image_label = tk.Label(image_frame, text="No image loaded", 
                                  bg="white", relief=tk.SUNKEN)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text frame
        text_frame = tk.LabelFrame(content_frame, text="Extracted Text", font=("Arial", 10, "bold"))
        text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                                 font=("Arial", 11))
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                            relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Store image path
        self.image_path = None
        
    def load_image(self):
        """Load an image file"""
        file_types = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=file_types
        )
        
        if filename:
            try:
                self.image_path = filename
                
                # Load and display image
                image = Image.open(filename)
                
                # Resize image to fit in the frame (max 300x300)
                image.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                self.image_label.configure(image=photo, text="")
                self.image_label.image = photo  # Keep a reference
                
                self.extract_button.config(state=tk.NORMAL)
                self.status_var.set(f"Image loaded: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                self.status_var.set("Error loading image")
    
    def extract_text(self):
        """Extract text from the loaded image using OCR"""
        if not self.image_path:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        try:
            self.status_var.set("Extracting text...")
            self.root.update()
            
            # Read image using OpenCV
            image = cv2.imread(self.image_path)
            
            # Convert to RGB (pytesseract expects RGB)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Use pytesseract to extract text
            # You can customize OCR configuration here
            custom_config = r'--oem 3 --psm 6'
            extracted_text = pytesseract.image_to_string(image_rgb, config=custom_config)
            
            # Display extracted text
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(1.0, extracted_text)
            
            if extracted_text.strip():
                self.play_button.config(state=tk.NORMAL)
                self.status_var.set("Text extracted successfully")
            else:
                self.status_var.set("No text found in image")
                messagebox.showinfo("Info", "No text was detected in the image")
                
        except Exception as e:
            messagebox.showerror("Error", f"OCR failed: {str(e)}")
            self.status_var.set("OCR extraction failed")
    
    def play_text(self):
        """Convert text to speech and play it"""
        text = self.text_area.get(1.0, tk.END).strip()
        
        if not text:
            messagebox.showwarning("Warning", "No text to read")
            return
        
        if self.is_speaking:
            messagebox.showinfo("Info", "Already speaking. Please wait or stop current playback.")
            return
        
        # Start speech in a separate thread to avoid freezing the GUI
        speech_thread = threading.Thread(target=self._speak_text, args=(text,))
        speech_thread.daemon = True
        speech_thread.start()
    
    def _speak_text(self, text):
        """Internal method to handle text-to-speech"""
        try:
            self.is_speaking = True
            self.play_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("Speaking...")
            
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
        except Exception as e:
            messagebox.showerror("Error", f"Text-to-speech failed: {str(e)}")
        finally:
            self.is_speaking = False
            self.play_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("Ready")
    
    def stop_speech(self):
        """Stop current speech"""
        try:
            self.tts_engine.stop()
            self.is_speaking = False
            self.play_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("Speech stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop speech: {str(e)}")
    
    def clear_text(self):
        """Clear the text area"""
        self.text_area.delete(1.0, tk.END)
        self.status_var.set("Text cleared")

def main():
    # Check if required libraries are available
    try:
        import pytesseract
        import pyttsx3
        import cv2
    except ImportError as e:
        print(f"Missing required library: {e}")
        print("\nPlease install required packages:")
        print("pip install pytesseract pyttsx3 opencv-python pillow")
        print("\nAlso install Tesseract OCR:")
        print("- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("- Ubuntu/Debian: sudo apt install tesseract-ocr")
        print("- macOS: brew install tesseract")
        return
    
    root = tk.Tk()
    app = OCRTextToSpeechApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
