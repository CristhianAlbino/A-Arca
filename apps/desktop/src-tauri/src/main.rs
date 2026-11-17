// ARCA desktop shell.
//
// Starts the local engine (Python) when the window opens, reads its single
// "ready" line from stdout (port + session token), hands those to the UI via
// the `engine_info` command, and stops the engine when the app exits.
// The token never appears on a command line and is only known to this process.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use serde::Serialize;
use tauri::{AppHandle, Manager, RunEvent, State};

#[derive(Clone, Default, Serialize)]
struct EngineInfo {
    port: Option<u16>,
    token: Option<String>,
    error: Option<String>,
}

#[derive(Default)]
struct Engine {
    child: Mutex<Option<Child>>,
    info: Mutex<EngineInfo>,
}

#[tauri::command]
fn engine_info(engine: State<'_, Engine>) -> EngineInfo {
    engine.info.lock().expect("engine info lock").clone()
}

/// In development: `python -m arca_engine` from the repository (engine/.venv if present).
/// In the installed app: the PyInstaller build shipped in the resources folder.
fn engine_command(app: &AppHandle) -> Result<Command, String> {
    if cfg!(debug_assertions) {
        let engine_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../engine");
        let venv_python = if cfg!(windows) {
            engine_dir.join(".venv").join("Scripts").join("python.exe")
        } else {
            engine_dir.join(".venv").join("bin").join("python")
        };
        let python = if venv_python.exists() {
            venv_python
        } else if cfg!(windows) {
            PathBuf::from("python")
        } else {
            PathBuf::from("python3")
        };
        let mut cmd = Command::new(python);
        cmd.args(["-m", "arca_engine", "--sidecar"])
            .current_dir(engine_dir);
        Ok(cmd)
    } else {
        let dir = app
            .path()
            .resource_dir()
            .map_err(|e| format!("Pasta de recursos não encontrada: {e}"))?
            .join("engine");
        let exe = if cfg!(windows) {
            dir.join("arca-engine.exe")
        } else {
            dir.join("arca-engine")
        };
        let mut cmd = Command::new(exe);
        cmd.arg("--sidecar").current_dir(dir);
        Ok(cmd)
    }
}

fn start_engine(app: &AppHandle) -> Result<(), String> {
    let mut cmd = engine_command(app)?;
    cmd.stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }

    let mut child = cmd
        .spawn()
        .map_err(|e| format!("Não foi possível iniciar o motor da ARCA: {e}"))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "O motor não abriu a saída padrão.".to_string())?;

    let handle = app.clone();
    std::thread::spawn(move || {
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            let Ok(value) = serde_json::from_str::<serde_json::Value>(&line) else {
                continue;
            };
            if value.get("event").and_then(|e| e.as_str()) != Some("ready") {
                continue;
            }
            let engine = handle.state::<Engine>();
            let mut info = engine.info.lock().expect("engine info lock");
            info.port = value
                .get("port")
                .and_then(|p| p.as_u64())
                .and_then(|p| u16::try_from(p).ok());
            info.token = value
                .get("token")
                .and_then(|t| t.as_str())
                .map(String::from);
        }
        // stdout closed: the engine stopped.
        let engine = handle.state::<Engine>();
        let mut info = engine.info.lock().expect("engine info lock");
        if info.error.is_none() {
            info.error = Some("O motor da ARCA foi encerrado.".into());
        }
        info.port = None;
    });

    *app.state::<Engine>()
        .child
        .lock()
        .expect("engine child lock") = Some(child);
    Ok(())
}

fn stop_engine(app: &AppHandle) {
    let child = app
        .state::<Engine>()
        .child
        .lock()
        .expect("engine child lock")
        .take();
    if let Some(mut child) = child {
        // Closing stdin asks the engine to exit on its own; kill makes sure it does.
        drop(child.stdin.take());
        let _ = child.kill();
        let _ = child.wait();
    }
}

fn main() {
    let app = tauri::Builder::default()
        .manage(Engine::default())
        .setup(|app| {
            if let Err(err) = start_engine(app.handle()) {
                app.state::<Engine>()
                    .info
                    .lock()
                    .expect("engine info lock")
                    .error = Some(err);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![engine_info])
        .build(tauri::generate_context!())
        .expect("erro ao iniciar a ARCA");

    app.run(|handle, event| {
        if let RunEvent::Exit = event {
            stop_engine(handle);
        }
    });
}
