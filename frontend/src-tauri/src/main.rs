// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::path::PathBuf;
use std::process::Command;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

const CREATE_NO_WINDOW: u32 = 0x08000000;

enum EngineRunner {
    CompiledExe(PathBuf),
    PythonScript(PathBuf, PathBuf),
}

fn resolve_engine() -> EngineRunner {
    let current_dir = env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| PathBuf::from("."));

    // 1. Derlenmiş motor
    let direct_engine = current_dir.join("stegocrypt_engine").join("stegocrypt_engine.exe");
    if direct_engine.exists() {
        return EngineRunner::CompiledExe(direct_engine);
    }

    let dist_engine = current_dir.join("dist").join("stegocrypt_engine").join("stegocrypt_engine.exe");
    if dist_engine.exists() {
        return EngineRunner::CompiledExe(dist_engine);
    }

    let project_dist = PathBuf::from(r"C:\Users\Turkay\Desktop\StegoCrypt-1.0.0\frontend\src-tauri\dist\stegocrypt_engine\stegocrypt_engine.exe");
    if project_dist.exists() {
        return EngineRunner::CompiledExe(project_dist);
    }

    // 2. Fallback: Konsolsuz Python (pythonw.exe)
    let conda_pythonw = PathBuf::from(r"C:\Users\Turkay\anaconda3\envs\env\pythonw.exe");
    let script_path = PathBuf::from(r"C:\Users\Turkay\Desktop\StegoCrypt-1.0.0\frontend\src-tauri\cli_bridge.py");

    EngineRunner::PythonScript(conda_pythonw, script_path)
}

fn build_command() -> Command {
    let mut cmd = match resolve_engine() {
        EngineRunner::CompiledExe(exe_path) => Command::new(exe_path),
        EngineRunner::PythonScript(py_path, script_path) => {
            let mut c = Command::new(py_path);
            c.arg(script_path);
            c
        }
    };

    #[cfg(windows)]
    cmd.creation_flags(CREATE_NO_WINDOW);

    cmd
}

#[tauri::command]
async fn analyze_capacity(cover_path: String, secret_path: String) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let mut cmd = build_command();
        cmd.arg("analyze").arg("--cover").arg(&cover_path);

        if !secret_path.is_empty() {
            cmd.arg("--secret").arg(&secret_path);
        }

        let output = cmd.output().map_err(|e| format!("Motor başlatılamadı: {}", e))?;
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        if !stderr.is_empty() && stdout.trim().is_empty() {
            return Err(format!("Motor Hatası: {}", stderr));
        }
        Ok(stdout)
    })
    .await
    .map_err(|e| format!("İş parçacığı hatası: {}", e))?
}

#[tauri::command]
async fn run_engine_embed(
    cover_path: String,
    secret_path: String,
    output_path: String,
    password: String,
    use_upscale: bool,
    bit_depth: u8,
) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let mut cmd = build_command();
        cmd.arg("embed")
            .arg("--cover")
            .arg(&cover_path)
            .arg("--secret")
            .arg(&secret_path)
            .arg("--output")
            .arg(&output_path)
            .arg("--password")
            .arg(&password)
            .arg("--bit-depth")
            .arg(bit_depth.to_string());

        if use_upscale {
            cmd.arg("--upscale");
        }

        let output = cmd.output().map_err(|e| format!("Motor başlatılamadı: {}", e))?;
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        if !stderr.is_empty() && stdout.trim().is_empty() {
            return Err(format!("Motor Hatası: {}", stderr));
        }
        Ok(stdout)
    })
    .await
    .map_err(|e| format!("İş parçacığı hatası: {}", e))?
}

#[tauri::command]
async fn run_engine_extract(
    stego_path: String,
    output_dir: String,
    password: String,
) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let mut cmd = build_command();
        cmd.arg("extract")
            .arg("--stego")
            .arg(&stego_path)
            .arg("--outdir")
            .arg(&output_dir)
            .arg("--password")
            .arg(&password);

        let output = cmd.output().map_err(|e| format!("Motor başlatılamadı: {}", e))?;
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        if !stderr.is_empty() && stdout.trim().is_empty() {
            return Err(format!("Motor Hatası: {}", stderr));
        }
        Ok(stdout)
    })
    .await
    .map_err(|e| format!("İş parçacığı hatası: {}", e))?
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            analyze_capacity,
            run_engine_embed,
            run_engine_extract
        ])
        .run(tauri::generate_context!())
        .expect("Tauri uygulaması başlatılırken hata oluştu");
}