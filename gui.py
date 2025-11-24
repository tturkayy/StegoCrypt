import customtkinter as ctk
from tkinter import filedialog, messagebox
import crypto
import stego
import os
import struct
import threading
import sys
import re
import webbrowser


def resource_path(relative_path):
    """
    Returns the absolute path of a resource.
    This ensures compatibility with PyInstaller one-file builds.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    """
    Main GUI application for StegoCrypt.
    Handles embedding encrypted data into an image and extracting/decrypting it.
    """

    def __init__(self):
        """
        Initializes the main window, theme, tabs, UI components, variables,
        event bindings and footer area.
        """
        super().__init__()

        self.title("StegoCrypt")
        self.geometry("700x750")
        self.minsize(700, 750)

        try:
            self.iconbitmap(resource_path("app.ico"))
        except Exception as e:
            print(f"Icon warning: {e}")

        self.target_image_path = None
        self.secret_file_path = None
        self.encrypted_image_path = None

        self.password_var = ctk.StringVar()
        self.password_var.trace_add("write", self.check_password_realtime)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_hide = self.tabview.add("  Encrypt & Embed  ")
        self.tab_reveal = self.tabview.add("  Decrypt & Extract  ")

        self.setup_hide_tab()
        self.setup_reveal_tab()

        # Status/Progress/Footer
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(side="bottom", fill="x", padx=20, pady=10)

        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Ready", text_color="gray70", anchor="w")
        self.lbl_status.pack(side="top", fill="x", pady=(0, 5))

        self.progress = ctk.CTkProgressBar(self.status_frame, orientation="horizontal", height=12)
        self.progress.pack(side="top", fill="x")
        self.progress.set(0)

        self.lbl_footer = ctk.CTkLabel(
            self.status_frame,
            text="Developed by tturkayy",
            text_color="gray50",
            font=("Roboto", 11),
            cursor="hand2"
        )
        self.lbl_footer.pack(side="top", pady=(15, 0))

        self.lbl_footer.bind("<Button-1>", lambda e: self.open_github())
        self.lbl_footer.bind("<Enter>", lambda e: self.lbl_footer.configure(text_color="#3B8ED0"))
        self.lbl_footer.bind("<Leave>", lambda e: self.lbl_footer.configure(text_color="gray50"))

    def open_github(self):
        """Opens developer GitHub profile."""
        webbrowser.open("https://github.com/tturkayy")

    def validate_password(self, password):
        """
        Validates password strength.
        Returns (True, "") if strong, otherwise (False, <reason>).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter (A-Z)."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter (a-z)."
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit (0-9)."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character (!@#$%)."
        return True, ""

    def check_password_realtime(self, *args):
        """
        Updates password feedback label dynamically
        while the user types into the password field.
        """
        password = self.password_var.get()
        is_valid, _ = self.validate_password(password)

        if is_valid:
            self.lbl_pass_info.configure(
                text="✓ Excellent! Password meets all requirements.",
                text_color="#2CC985"
            )
        else:
            self.lbl_pass_info.configure(
                text="⚠️ Requirements: Min 8 chars, 1 Uppercase, 1 Lowercase, 1 Digit, 1 Special (!@#$)",
                text_color="#FFB347"
            )

    def setup_hide_tab(self):
        """Builds the interface for 'Encrypt & Embed' tab."""
        frame_files = ctk.CTkFrame(self.tab_hide)
        frame_files.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(frame_files, text="1. Cover Image (PNG/JPG)", font=("Roboto", 14, "bold")).pack(anchor="w",
                                                                                                     padx=15,
                                                                                                     pady=(15, 5))

        sub_frame_img = ctk.CTkFrame(frame_files, fg_color="transparent")
        sub_frame_img.pack(fill="x", padx=15, pady=(0, 10))

        self.btn_target_img = ctk.CTkButton(sub_frame_img, text="Select Image", width=120,
                                            command=self.select_target_image)
        self.btn_target_img.pack(side="left")
        self.lbl_target_img = ctk.CTkLabel(sub_frame_img, text="No file selected", text_color="gray60")
        self.lbl_target_img.pack(side="left", padx=10)

        ctk.CTkLabel(frame_files, text="2. Secret File (PDF, ZIP, Any)", font=("Roboto", 14, "bold")).pack(anchor="w",
                                                                                                           padx=15,
                                                                                                           pady=(10, 5))

        sub_frame_file = ctk.CTkFrame(frame_files, fg_color="transparent")
        sub_frame_file.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_secret_file = ctk.CTkButton(sub_frame_file, text="Select File", width=120, fg_color="#7b2cbf",
                                             hover_color="#5a189a", command=self.select_secret_file)
        self.btn_secret_file.pack(side="left")
        self.lbl_secret_file = ctk.CTkLabel(sub_frame_file, text="No file selected", text_color="gray60")
        self.lbl_secret_file.pack(side="left", padx=10)

        frame_sec = ctk.CTkFrame(self.tab_hide)
        frame_sec.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(frame_sec, text="3. Security Configuration", font=("Roboto", 14, "bold")).pack(anchor="w", padx=15,
                                                                                                    pady=(15, 5))

        self.entry_pass_hide = ctk.CTkEntry(
            frame_sec,
            show="*",
            placeholder_text="Enter a strong password...",
            textvariable=self.password_var
        )
        self.entry_pass_hide.pack(fill="x", padx=15, pady=(5, 5))

        info_text = "⚠️ Requirements: Min 8 chars, 1 Uppercase, 1 Lowercase, 1 Digit, 1 Special (!@#$)"
        self.lbl_pass_info = ctk.CTkLabel(frame_sec, text=info_text, text_color="#FFB347", font=("Roboto", 11))
        self.lbl_pass_info.pack(anchor="w", padx=15, pady=(0, 15))

        self.btn_hide = ctk.CTkButton(self.tab_hide, text="🔒 ENCRYPT & EMBED",
                                      font=("Roboto", 16, "bold"), height=50, fg_color="#2b9348",
                                      hover_color="#007f5f",
                                      command=self.start_embedding_thread)
        self.btn_hide.pack(padx=10, pady=20, fill="x")

    def setup_reveal_tab(self):
        """Builds the interface for 'Decrypt & Extract' tab."""
        frame_src = ctk.CTkFrame(self.tab_reveal)
        frame_src.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(frame_src, text="Encrypted Image Source", font=("Roboto", 14, "bold")).pack(anchor="w", padx=15,
                                                                                                 pady=(15, 5))

        sub_frame_src = ctk.CTkFrame(frame_src, fg_color="transparent")
        sub_frame_src.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_enc_img = ctk.CTkButton(sub_frame_src, text="Select Image", width=120,
                                         command=self.select_encrypted_image)
        self.btn_enc_img.pack(side="left")
        self.lbl_enc_img = ctk.CTkLabel(sub_frame_src, text="No file selected", text_color="gray60")
        self.lbl_enc_img.pack(side="left", padx=10)

        frame_auth = ctk.CTkFrame(self.tab_reveal)
        frame_auth.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(frame_auth, text="Decryption Key", font=("Roboto", 14, "bold")).pack(anchor="w", padx=15,
                                                                                          pady=(15, 5))

        self.entry_pass_reveal = ctk.CTkEntry(
            frame_auth,
            show="*",
            placeholder_text="Enter the password used for encryption..."
        )
        self.entry_pass_reveal.pack(fill="x", padx=15, pady=(5, 15))

        self.btn_reveal = ctk.CTkButton(self.tab_reveal, text="🔓 DECRYPT & EXTRACT",
                                        font=("Roboto", 16, "bold"), height=50, fg_color="#e07a5f",
                                        hover_color="#d35400",
                                        command=self.start_extracting_thread)
        self.btn_reveal.pack(padx=10, pady=20, fill="x")

    def select_target_image(self):
        """Opens file dialog for selecting the cover image."""
        f = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if f:
            self.target_image_path = f
            self.lbl_target_img.configure(text=os.path.basename(f), text_color="white")

    def select_secret_file(self):
        """Prompts user to choose the secret file to embed."""
        f = filedialog.askopenfilename()
        if f:
            self.secret_file_path = f
            self.lbl_secret_file.configure(text=os.path.basename(f), text_color="white")

    def select_encrypted_image(self):
        """Prompts user to choose an image containing embedded encrypted data."""
        f = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
        if f:
            self.encrypted_image_path = f
            self.lbl_enc_img.configure(text=os.path.basename(f), text_color="white")

    def update_progress_gui(self, value):
        """
        Updates GUI progress bar and status text during embedding/extraction.
        """
        self.progress.set(value)
        self.lbl_status.configure(text=f"Processing... {int(value * 100)}%")

    def lock_ui(self, is_locked):
        """
        Enables/disables main action buttons to prevent user interaction
        during long operations.
        """
        state = "disabled" if is_locked else "normal"
        self.btn_hide.configure(state=state)
        self.btn_reveal.configure(state=state)
        if not is_locked:
            self.lbl_status.configure(text="Operation Completed Successfully.")

    def start_embedding_thread(self):
        """
        Validates input, password, file selections and launches
        the embedding process in a background thread.
        """
        if not self.target_image_path or not self.secret_file_path:
            messagebox.showerror("Error", "Please select an image and a file.")
            return

        password = self.entry_pass_hide.get()
        if not password:
            messagebox.showerror("Error", "Please enter a password.")
            return

        is_valid, error_msg = self.validate_password(password)
        if not is_valid:
            messagebox.showwarning("Weak Password", error_msg)
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not save_path:
            return

        self.lock_ui(True)
        threading.Thread(target=self.run_embedding, args=(save_path,)).start()

    def run_embedding(self, save_path):
        """
        Reads secret file, prepares payload, encrypts it,
        and embeds encrypted bytes into the cover image.
        """
        try:
            sifre = self.entry_pass_hide.get()
            with open(self.secret_file_path, "rb") as f:
                file_bytes = f.read()

            filename = os.path.basename(self.secret_file_path).encode('utf-8')
            header = struct.pack('I', len(filename))
            full_payload = header + filename + file_bytes

            self.lbl_status.configure(text="Encrypting data...")
            encrypted_payload = crypto.encrypt_message(full_payload, sifre)

            self.lbl_status.configure(text="Embedding data into pixels...")
            stego.encode_image(self.target_image_path, encrypted_payload, save_path, self.update_progress_gui)

            messagebox.showinfo("Success", "Data encrypted and embedded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")
        finally:
            self.lock_ui(False)

    def start_extracting_thread(self):
        """
        Launches the extraction process in a background thread
        after basic validation.
        """
        if not self.encrypted_image_path or not self.entry_pass_reveal.get():
            messagebox.showerror("Error", "Image and password are required.")
            return

        self.lock_ui(True)
        threading.Thread(target=self.run_extracting).start()

    def run_extracting(self):
        """
        Reads embedded cipher bytes from the selected image,
        decrypts them using the user-provided password,
        reconstructs original file and prompts user to save it.
        """
        try:
            sifre = self.entry_pass_reveal.get()

            self.lbl_status.configure(text="Scanning image bits...")
            encrypted_data = stego.decode_image(self.encrypted_image_path, self.update_progress_gui)

            self.lbl_status.configure(text="Decrypting data...")
            decrypted_payload = crypto.decrypt_message(encrypted_data, sifre)

            if decrypted_payload == b"ERROR":
                raise Exception("Invalid Password or Corrupted Data!")

            filename_len = struct.unpack('I', decrypted_payload[:4])[0]
            filename = decrypted_payload[4: 4 + filename_len].decode('utf-8')
            file_data = decrypted_payload[4 + filename_len:]

            save_path = filedialog.asksaveasfilename(initialfile=filename, title="Save Extracted File")
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(file_data)

                messagebox.showinfo("Success", f"File extracted: {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            self.lock_ui(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
