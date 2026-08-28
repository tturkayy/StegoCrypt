# StegoCrypt Frontend

Desktop UI and native Rust bridge built with Tauri v2.

## Structure
* `src/`: React + Tailwind CSS interface
* `src-tauri/`: Rust runtime and backend bridge invoking the Python engine

## Development

Install dependencies:
    npm install

Run UI in browser:
    npm run dev

Run desktop app in dev mode:
    npm run tauri dev

Build installer (.msi / .exe):
    npm run tauri build
