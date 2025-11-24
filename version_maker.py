"""
StegoCrypt Build Utility: Version Info Generator
------------------------------------------------
This script generates the 'file_version_info.txt' file required by PyInstaller
to embed metadata into the final Windows executable (.exe).

It defines properties such as:
- File Version (e.g., 1.0.0.0)
- Company Name & Copyright
- Product Name & Description

Usage:
    Run this script once before building the executable:
    $ python version_maker.py

Output:
    Creates/Overwrites 'file_version_info.txt' in the root directory.

Author: Turkay Yildirim
License: MIT
"""

import pyinstaller_versionfile

def generate_version_file():
    pyinstaller_versionfile.create_versionfile(
        output_file="file_version_info.txt",
        version="1.0.0.0",
        company_name="Turkay Yildirim",
        file_description="Encrypted Steganography Tool",
        internal_name="StegoCrypt",
        legal_copyright="© 2025 Turkay Yildirim",
        original_filename="StegoCrypt.exe",
        product_name="StegoCrypt"
    )
    print("✅ Build Artifact Created: 'file_version_info.txt' generated successfully.")

if __name__ == "__main__":
    generate_version_file()