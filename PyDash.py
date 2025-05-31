import os
import requests
import subprocess
import time
from flask import Flask, render_template_string, request
import socket
import json
from tkinter import Tk, filedialog

app = Flask(__name__)

CONFIG_PATH = "config.json"

# Get cross-platform default Documents path
DEFAULT_SCRIPT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "PyDash")

# Ensure the default directory exists
os.makedirs(DEFAULT_SCRIPT_DIR, exist_ok=True)

def load_script_dir():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                path = config.get("SCRIPT_DIR", DEFAULT_SCRIPT_DIR)
                if os.path.isdir(path):
                    return path
        except json.JSONDecodeError:
            print("⚠️ config.json is invalid, using default directory.")
    return DEFAULT_SCRIPT_DIR

def save_script_dir(path):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"SCRIPT_DIR": path}, f, indent=2)

# Global directory used by all routes
SCRIPT_DIR = load_script_dir()

# ---------------------- GitHub Version Fetch ----------------------
def fetch_python_versions():
    try:
        url = "https://api.github.com/repos/actions/python-versions/releases"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            releases = response.json()
            raw_versions = {r['tag_name'].lstrip('v').split('-')[0] for r in releases}
            versions = sorted(
                raw_versions,
                key=lambda v: tuple(map(int, v.split("."))),
                reverse=True
            )
            return versions
    except Exception:
        pass
    return ["3.12", "3.11", "3.10", "3.9", "3.8"]

# ---------------------- Choose Directory ----------------------
def pick_directory():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Python Script Directory")
    if folder_path:
        with open(CONFIG_PATH, "w") as f:
            json.dump({"SCRIPT_DIR": folder_path}, f, indent=2)
        print(f"✅ Saved to config.json:\n{folder_path}")
    else:
        print("❌ No folder selected.")

@app.route("/run-folder-picker")
def run_folder_picker():
    subprocess.Popen(["python", "set_directory.py"])
    return "<p>✅ Folder picker launched. Please return and refresh once complete.</p><a href='/settings'>Back</a>"


# ---------------------- Shared HTML ----------------------
sidebar_html = """
<div class="sidebar">
    <button class="menu-button" onclick="location.href='/'">🏠 Dashboard</button>
    <!-- <button class="menu-button" onclick="location.href='/create'">🆕 Create</button> --!>
    <button class="menu-button" onclick="location.href='/scripts'">📄 Scripts</button>
    <button class="menu-button" onclick="location.href='/scheduled'">⏰ Scheduled</button>
    <button class="menu-button" onclick="location.href='/settings'">⚙️ Settings</button>
</div>
"""

base_css = """
<style>
    body {
        margin: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #1e1e1e;
        color: #f1f1f1;
    }
    .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        width: 220px;
        height: 100%;
        background-color: #2e2e2e;
        display: flex;
        flex-direction: column;
        padding-top: 40px;
        border-right: 1px solid #444;
    }
    .menu-button {
        padding: 15px 20px;
        text-align: left;
        background: none;
        border: none;
        outline: none;
        color: #ccc;
        font-size: 1em;
        cursor: pointer;
        transition: background 0.2s;
    }
    .menu-button:hover {
        background-color: #3a3a3a;
        color: #fff;
    }
    .main {
        margin-left: 220px;
        padding: 20px;
    }
    .header {
        font-size: 1.6em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .file-list {
        list-style: none;
        padding: 0;
    }
    .file-list li {
        background-color: #2a2a2a;
        margin-bottom: 10px;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #444;
        font-family: monospace;
        transition: background 0.2s;
    }
    .file-list li:hover {
        background-color: #3b3b3b;
    }
    p {
        color: #ccc;
    }
</style>
"""

# ---------------------- Routes ----------------------

@app.route("/")
def dashboard():
    hostname = socket.gethostname()
    return render_template_string(f"""
    <!doctype html><html><head><title>Dashboard</title>{base_css}</head><body>
        {sidebar_html}
        <div class="main">
            <div class="header">Python Dashboard</div>
            <p>This dashboard is served from <strong>{hostname}</strong>.</p>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
                <div style="background-color:#2a2a2a; padding:20px; border-radius:8px; border:1px solid #444;">
                    <h3>🕒 Recently Run</h3>
                    <p>No recent runs.</p>
                </div>
                <div style="background-color:#2a2a2a; padding:20px; border-radius:8px; border:1px solid #444;">
                    <h3>⏰ Scheduled Scripts</h3>
                    <p>No scheduled scripts.</p>
                </div>
                <div style="background-color:#2a2a2a; padding:20px; border-radius:8px; border:1px solid #444;">
                    <h3>🔜 Next Scheduled Run</h3>
                    <p>Nothing scheduled.</p>
                </div>
            </div>
        </div>
    </body></html>
    """)

@app.route("/create")
def create():
    versions = fetch_python_versions()
    default_version = versions[0]
    options_html = "".join(
        f'<option value="{v}" {"selected" if v == default_version else ""}>{v}</option>' for v in versions
    )

    return render_template_string(f"""
    <!doctype html>
    <html>
    <head>
        <title>Create</title>
        {base_css}
        <style>
            #editor {{
                height: 600px;
                width: 100%;
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #1e1e1e;
            }}
            .editor-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            .filename-label {{
                font-family: monospace;
                font-size: 1em;
                color: #ccc;
            }}
            .version-select {{
                font-size: 1em;
                background-color: #2e2e2e;
                color: #fff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }}
            .save-btn {{
                position: fixed;
                bottom: 20px;
                right: 40px;
                padding: 10px 20px;
                font-size: 1em;
                background-color: #444;
                color: #fff;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            .save-btn:hover {{
                background-color: #555;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js"></script>
    </head>
    <body>
        {sidebar_html}
        <div class="main">
            <div class="header">Create</div>
            <div class="editor-header">
                <span id="filename-display" class="filename-label">Unsaved script</span>
                <div>
                    <label for="version" style="margin-right: 5px;">Version:</label>
                    <select id="version" class="version-select">{options_html}</select>
                </div>
            </div>
            <div id="editor"></div>
            <button class="save-btn" onclick="promptFilename()">💾 Save</button>
        </div>
        <script>
        let saved = false;
        let filename = null;
        let originalCode = `# Write your Python code here`;

        window.addEventListener('beforeunload', function (e) {{
            if (!saved && window.editor && window.editor.getValue() !== originalCode) {{
                e.preventDefault();
                e.returnValue = '';
            }}
        }});

        require.config({{ paths: {{ vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' }} }});
        require(['vs/editor/editor.main'], function () {{
            window.editor = monaco.editor.create(document.getElementById('editor'), {{
                value: originalCode,
                language: 'python',
                theme: 'vs-dark',
                fontSize: 14,
                minimap: {{ enabled: false }},
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true
            }});
        }});

        function promptFilename() {{
            if (!filename) {{
                const input = prompt("Enter filename (without .py):");
                if (!input) return;
                filename = input.endsWith(".py") ? input : input + ".py";
            }}
            saveCode(false);
        }}

        function saveCode(overwrite) {{
            const code = window.editor.getValue();
            const pythonVersion = document.getElementById("version").value;

            fetch('/save-script', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    content: code,
                    filename: filename,
                    python_version: pythonVersion,
                    overwrite: overwrite
                }})
            }})
            .then(res => res.text())
            .then(msg => {{
                if (msg === "EXISTS") {{
                    if (confirm(`A script named "${{filename}}" already exists. Overwrite?`)) {{
                        saveCode(true);
                    }}
                    return;
                }}
                alert(msg);
                saved = true;
                filename = null;
                document.getElementById("filename-display").innerText = "Unsaved script";
                window.editor.setValue(originalCode); // Reset to blank
            }});
        }}
        </script>
    </body>
    </html>
    """)

@app.route("/save-script", methods=["POST"])
def save_script():
    data = request.get_json()
    content = data.get("content", "")
    name = data.get("filename", "").strip()
    version = data.get("python_version", "3.12").split("-")[0]
    overwrite = data.get("overwrite", False)

    if not name.endswith(".py"):
        name += ".py"

    script_dir = os.path.join(SCRIPT_DIR, name[:-3])
    os.makedirs(script_dir, exist_ok=True)

    script_path = os.path.join(script_dir, name)

    if os.path.exists(script_path) and not overwrite:
        return "EXISTS", 200

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)

    uv_cfg_path = os.path.join(script_dir, "uv.cfg")
    uv_initialized = os.path.exists(uv_cfg_path)

    if not uv_initialized:
        try:
            subprocess.run(["uv", "init", "--python", version], cwd=script_dir, check=True)
            default_main_path = os.path.join(script_dir, "main.py")
            if os.path.exists(default_main_path) and default_main_path != script_path:
                os.replace(default_main_path, script_path)
        except subprocess.CalledProcessError as e:
            return f"❌ UV init failed: {e}", 500

    # Optional: install requirements if present
    req_path = os.path.join(script_dir, "requirements.txt")
    if os.path.exists(req_path):
        try:
            subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], cwd=script_dir, check=True)
        except subprocess.CalledProcessError as e:
            return f"⚠️ Saved, but failed to update dependencies: {e}", 500

    return "✅ Script saved.\n✅ UV virtual environment created."

@app.route("/scripts")
def list_scripts():
    dirs = os.listdir(SCRIPT_DIR)
    py_dirs = [
        d for d in dirs
        if os.path.isdir(os.path.join(SCRIPT_DIR, d)) and
        os.path.exists(os.path.join(SCRIPT_DIR, d, f"{d}.py"))
    ]

    rows = ""
    for d in py_dirs:
        script_path = os.path.join(SCRIPT_DIR, d, f"{d}.py")
        created = os.path.getctime(script_path)
        modified = os.path.getmtime(script_path)
        created_str = f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(created))}"
        modified_str = f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(modified))}"

        rows += f"""
        <tr>
            <td>{d}.py</td>
            <td>{created_str}</td>
            <td>{modified_str}</td>
            <td style="text-align:right;">
                <a href="/run-script/{d}" class="action-button">▶️ Run</a>
                <a href="/edit-script/{d}" class="action-button">✏️ Edit</a>
                <a href="/delete-script/{d}" class="action-button danger">🗑️ Delete</a>
            </td>
        </tr>
        """

    return render_template_string(f"""
    <!doctype html><html><head><title>Scripts</title>{base_css}
    <style>
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            border-bottom: 1px solid #444;
        }}
        th {{
            background-color: #2e2e2e;
            text-align: left;
        }}
        tr:hover {{
            background-color: #333;
        }}
        .action-button {{
            margin-left: 8px;
            padding: 6px 12px;
            background-color: #444;
            border-radius: 4px;
            color: white;
            text-decoration: none;
        }}
        .action-button:hover {{
            background-color: #555;
        }}
        .danger {{
            background-color: #b33a3a;
        }}
        .danger:hover {{
            background-color: #cc4444;
        }}
        .create-button {{
            float: right;
            padding: 8px 16px;
            margin-bottom: 10px;
            background-color: #4a90e2;
            color: white;
            border-radius: 4px;
            text-decoration: none;
            font-weight: bold;
        }}
        .create-button:hover {{
            background-color: #5aa0f0;
        }}
        .header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
    </style>
    </head><body>
        {sidebar_html}
        <div class="main">
            <div class="header-bar">
                <div class="header">Scripts</div>
                <a href="/create" class="create-button">➕ Create Script</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Date Created</th>
                        <th>Last Modified</th>
                        <th style="text-align:right;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </body></html>
    """)

@app.route("/view-script/<folder>/<filename>")
def view_script(folder, filename):
    full_path = os.path.join(SCRIPT_DIR, folder, filename)
    if not os.path.isfile(full_path):
        return "File not found", 404
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    highlighted = f"<pre style='white-space: pre-wrap; font-family: Consolas, monospace; color: #ddd;'>{content}</pre>"
    return render_template_string(f"""
    <!doctype html><html><head><title>{filename}</title>{base_css}</head><body>
        {sidebar_html}
        <div class="main">
            <div class="header">Viewing: {filename}</div>
            {highlighted}
        </div>
    </body></html>
    """)

@app.route("/scheduled")
def scheduled():
    return render_template_string(f"""
    <!doctype html><html><head><title>Scheduled</title>{base_css}</head><body>
        {sidebar_html}
        <div class="main">
            <div class="header">Scheduled Tasks</div>
            <p>No scheduled tasks yet.</p>
        </div>
    </body></html>
    """)

@app.route("/settings")
def settings():
    current_dir = SCRIPT_DIR

    return render_template_string(f"""
    <!doctype html><html><head><title>Settings</title>{base_css}</head><body>
        {sidebar_html}
        <div class="main">
            <div class="header">Settings</div>
            <p><strong>Script Directory:</strong></p>
            <input type="text" value="{current_dir}" disabled style="width: 100%; padding: 10px; background-color: #2e2e2e; color: #fff; border: 1px solid #555; border-radius: 4px; margin-bottom: 10px;" />
            <form method="GET" action="/run-folder-picker">
                <button type="submit" style="padding: 10px 20px; background-color: #444; color: #fff; border: none; border-radius: 4px;">📂 Browse</button>
            </form>
            <p>This will open a folder picker window. Restart the app to apply changes.</p>
        </div>
    </body></html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

