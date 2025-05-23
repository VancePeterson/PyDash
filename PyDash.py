import os
import requests
import subprocess
from flask import Flask, render_template_string, request
import socket

app = Flask(__name__)
SCRIPT_DIR = r"C:\Users\Vance\Desktop\Python"

# ---------------------- GitHub Version Fetch ----------------------
def fetch_python_versions():
    try:
        url = "https://api.github.com/repos/actions/python-versions/releases"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            releases = response.json()
            versions = sorted({r['tag_name'].lstrip('v').split('-')[0] for r in releases}, reverse=True)
            return versions
    except Exception:
        pass
    # Fallback list
    return ["3.12", "3.11", "3.10", "3.9", "3.8"]

# ---------------------- Shared HTML ----------------------
sidebar_html = """
<div class="sidebar">
    <button class="menu-button" onclick="location.href='/'">🏠 Dashboard</button>
    <button class="menu-button" onclick="location.href='/create'">🆕 Create</button>
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
                saveCode();
            }}

            function saveCode() {{
                const code = window.editor.getValue();
                const pythonVersion = document.getElementById("version").value;
                fetch('/save-script', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        content: code,
                        filename: filename,
                        python_version: pythonVersion
                    }})
                }})
                .then(res => res.text())
                .then(msg => {{
                    alert(msg);
                    saved = true;
                    document.getElementById("filename-display").innerText = filename;
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

    if not name.endswith(".py"):
        name += ".py"

    script_dir = os.path.join(SCRIPT_DIR, name[:-3])
    os.makedirs(script_dir, exist_ok=True)

    script_path = os.path.join(script_dir, name)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)

    uv_cfg_path = os.path.join(script_dir, "uv.cfg")
    uv_initialized = os.path.exists(uv_cfg_path)

    if not uv_initialized:
        try:
            subprocess.run(["uv", "init", "--python", version], cwd=script_dir, check=True)

            # After init, rename auto-generated main.py to your custom filename
            default_main_path = os.path.join(script_dir, "main.py")
            if os.path.exists(default_main_path) and default_main_path != script_path:
                os.replace(default_main_path, script_path)
        except subprocess.CalledProcessError as e:
            return f"❌ UV init failed: {e}", 500

    else:
        # If already initialized, just overwrite existing file
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Optional: install requirements if they exist
    req_path = os.path.join(script_dir, "requirements.txt")
    if os.path.exists(req_path):
        try:
            subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], cwd=script_dir, check=True)
        except subprocess.CalledProcessError as e:
            return f"⚠️ Saved, but failed to update dependencies: {e}", 500

    return f"✅ Script saved. UV env {'created and main.py renamed' if not uv_initialized else 'updated'} for {name}"

@app.route("/scripts")
def list_scripts():
    dirs = os.listdir(SCRIPT_DIR)
    py_dirs = [d for d in dirs if os.path.isdir(os.path.join(SCRIPT_DIR, d)) and os.path.exists(os.path.join(SCRIPT_DIR, d, f"{d}.py"))]
    return render_template_string(f"""
    <!doctype html><html><head><title>Scripts</title>{base_css}</head><body>
        {sidebar_html}
        <div class="main">
            <div class="header">Scripts</div>
            <ul class="file-list">
                {''.join(f'<li><a href="/view-script/{d}/{d}.py" style="color:inherit;text-decoration:none;">{d}</a></li>' for d in py_dirs)}
            </ul>
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
    return render_template_string(f"""
    <!doctype html><html><head><title>Settings</title>{base_css}</head><body>
        {sidebar_html}
        <div class="main">
            <div class="header">Settings</div>
            <p>Configure dashboard options here.</p>
        </div>
    </body></html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

