import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
from emotion import ExpressionDetection
from songs_list import emotion_songs


class ImageUploaderApp:
    def __init__(self, root):
        self._emotion_detected = None
        self.root = root
        self.root.title("Image Upload UI")
        self.root.geometry("500x600")

        self.label = tk.Label(root, text="No image selected")
        self.label.pack(pady=10)

        self.upload_button = tk.Button(root, text="Choose Image", command=self.choose_image)
        self.upload_button.pack(pady=5)

        self.submit_button = tk.Button(root, text="Submit", command=self.submit_image)
        self.submit_button.pack(pady=5)

        self.image_path = None
        self.image_label = tk.Label(root)
        self.image_label.pack(pady=10)

        self.emotion_label = tk.Label(root, text="", font=("Arial", 14), fg="blue")
        self.emotion_label.pack(pady=5)

        self.song_text = ScrolledText(root, height=10, width=50, font=("Arial", 10))
        self.song_text.pack(pady=10)

        self.emotion_detection = ExpressionDetection()

    def choose_image(self):
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp")]
        self.image_path = filedialog.askopenfilename(title="Select an Image", filetypes=filetypes)
        if self.image_path:
            self.label.config(text=f"Selected: {self.image_path.split('/')[-1]}")
            img = Image.open(self.image_path)
            img.thumbnail((200, 200))
            img = ImageTk.PhotoImage(img)
            self.image_label.configure(image=img)
            self.image_label.image = img

    def submit_image(self):
        if self.image_path:
            self._emotion_detected = self.emotion_detection.detect_image_expression(self.image_path)
            self.emotion_label.config(text=f"Detected Emotion: {self._emotion_detected.capitalize()}")
            print("Image successfully uploaded:", self.image_path)
            messagebox.showinfo("Success", f"Emotion Detected: {self._emotion_detected}")

            # Update song list
            self.song_text.delete('1.0', tk.END)
            songs = emotion_songs.get(self._emotion_detected.lower(), [])
            if songs:
                self.song_text.insert(tk.END, "\n".join(f"• {song}" for song in songs))
            else:
                self.song_text.insert(tk.END, "No songs available for this emotion.")
        else:
            messagebox.showwarning("No Image", "Please choose an image first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageUploaderApp(root)
    root.mainloop()
