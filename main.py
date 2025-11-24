"""
StegoCrypt: Advanced Image Steganography Tool
=============================================

This is the main entry point for the StegoCrypt application.
It initializes the Graphical User Interface (GUI) and starts the main event loop.

Application Overview:
---------------------
StegoCrypt allows users to securely encrypt files using AES-256 and hide them
within PNG images using Least Significant Bit (LSB) manipulation. It features
a multi-threaded architecture to ensure a responsive user experience.

Metadata:
---------
- Author:      Turkay Yildirim
- Version:     1.0.0 (Official Release)
- License:     MIT License
- Repository:  https://github.com/tturkayy/StegoCrypt
- Created:     November 2025

Dependencies:
-------------
- customtkinter
- Pillow (PIL)
- pycryptodome

Usage:
------
Run this script directly to launch the application:
    $ python main.py
"""

import sys
from gui import App

def main():
    """
    Initializes the main application window and starts the event loop.
    """
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print(f"Critical Error: Failed to launch application.\nDetails: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()