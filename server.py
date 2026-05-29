from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import sys
import platform
import socket
import urllib.parse
import threading
import time

# Global variables for simulation
allocated_memory = []

def run_cpu_load(seconds=10):
    end_time = time.time() + seconds
    while time.time() < end_time:
        # Tight loop to consume CPU
        _ = 123 * 456

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))
        sys.stdout.flush()

    def do_GET(self):
        global allocated_memory
        
        # Parse query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        action = query_params.get("action", [None])[0]
        status_message = None

        # Handle load simulation actions
        if action == "cpu":
            duration = int(query_params.get("duration", [10])[0])
            t = threading.Thread(target=run_cpu_load, args=(duration,))
            t.daemon = True
            t.start()
            status_message = f"🔥 Started CPU load simulation thread (100% core load) for {duration} seconds."
            
        elif action == "ram":
            mb = int(query_params.get("mb", [50])[0])
            try:
                # Create block_size arrays of 1MB each
                for _ in range(mb):
                    allocated_memory.append(bytearray(1024 * 1024))
                status_message = f"🟢 Successfully allocated {mb} MB of RAM. Total allocated blocks: {len(allocated_memory)} MB."
            except MemoryError:
                status_message = "❌ Memory allocation failed! Memory Limit reached."
                
        elif action == "clear_ram":
            mb_freed = len(allocated_memory)
            allocated_memory.clear()
            import gc
            gc.collect()
            status_message = f"🧹 Cleared {mb_freed} MB of simulated RAM from memory."

        # 1. OS & Kernel Details
        try:
            with open("/etc/os-release") as f:
                os_release = f.read()
        except Exception:
            os_release = platform.platform()
            
        kernel = platform.uname().release
        python_ver = sys.version
        
        # 2. User & UID
        try:
            import pwd
            uid = os.getuid()
            gid = os.getgid()
            username = pwd.getpwuid(uid).pw_name
        except Exception:
            uid = getattr(os, 'getuid', lambda: 'N/A')()
            gid = getattr(os, 'getgid', lambda: 'N/A')()
            username = 'N/A'
            
        # 3. Network Configuration
        hostname = socket.gethostname()
        try:
            ip_addr = socket.gethostbyname(hostname)
        except Exception:
            ip_addr = 'N/A'
            
        # 4. Cgroups Memory Limits
        mem_limit = "N/A"
        mem_usage = "N/A"
        if os.path.exists("/sys/fs/cgroup/memory.max"):
            try:
                with open("/sys/fs/cgroup/memory.max") as f:
                    mem_limit = f.read().strip()
                with open("/sys/fs/cgroup/memory.current") as f:
                    mem_usage = f.read().strip()
            except Exception:
                pass
        elif os.path.exists("/sys/fs/cgroup/memory/memory.limit_in_bytes"):
            try:
                with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
                    mem_limit = f.read().strip()
                with open("/sys/fs/cgroup/memory/memory.usage_in_bytes") as f:
                    mem_usage = f.read().strip()
            except Exception:
                pass

        # Convert memory values from bytes to MB if numeric
        try:
            mem_limit_mb = f"{int(mem_limit) / 1024 / 1024:.2f} MB"
        except ValueError:
            mem_limit_mb = mem_limit
        try:
            mem_usage_mb = f"{int(mem_usage) / 1024 / 1024:.2f} MB"
        except ValueError:
            mem_usage_mb = mem_usage

        # 5. Environment Variables
        env_rows = []
        for k, v in sorted(os.environ.items()):
            env_rows.append(f"<tr><td class='label'>{k}</td><td class='value'>{v}</td></tr>")
        env_table_content = "\n".join(env_rows)

        # 6. Filesystem list
        try:
            files = os.listdir(".")
            files_str = ", ".join(files)
        except Exception as e:
            files_str = str(e)
            
        # 7. Mounts
        try:
            with open("/proc/mounts") as f:
                mounts = [line.strip() for line in f.readlines() if line.strip()][:15]
            mounts_str = "\n".join(mounts)
        except Exception:
            mounts_str = "N/A"

        # Status alert banner
        status_banner = ""
        if status_message:
            status_banner = f"""
            <div style="background-color: #1e1b4b; border: 1px solid #312e81; color: #a5b4fc; padding: 1rem; border-radius: 8px; margin-bottom: 2rem; font-weight: 500;">
                {status_message}
            </div>
            """

        # Build HTML page
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Deployed Container Diagnostics</title>
    <style>
        body {{
            background-color: #09090b;
            color: #f4f4f5;
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            color: #3b82f6;
            border-bottom: 1px solid #27272a;
            padding-bottom: 0.5rem;
            margin-bottom: 2rem;
            font-size: 2rem;
            font-weight: 700;
        }}
        .card {{
            background-color: #18181b;
            border: 1px solid #27272a;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .card-title {{
            font-size: 1.15rem;
            font-weight: 600;
            color: #a1a1aa;
            margin-top: 0;
            margin-bottom: 1rem;
            border-bottom: 1px dashed #27272a;
            padding-bottom: 0.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        td {{
            padding: 0.5rem 0;
            vertical-align: top;
        }}
        td.label {{
            width: 30%;
            font-weight: 600;
            color: #71717a;
        }}
        td.value {{
            font-family: monospace;
            color: #e4e4e7;
            word-break: break-all;
        }}
        pre {{
            background-color: #09090b;
            border: 1px solid #27272a;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            color: #10b981;
            font-size: 0.875rem;
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-wrap: break-word;
        }}
        .btn {{
            display: inline-block;
            background-color: #27272a;
            color: #f4f4f5;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            border: 1px solid #3f3f46;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .btn:hover {{
            background-color: #3f3f46;
        }}
        .btn-cpu {{
            background-color: #7f1d1d;
            border-color: #991b1b;
        }}
        .btn-cpu:hover {{
            background-color: #991b1b;
        }}
        .btn-ram {{
            background-color: #064e3b;
            border-color: #065f46;
        }}
        .btn-ram:hover {{
            background-color: #065f46;
        }}
        .btn-clear {{
            background-color: #1e293b;
            border-color: #334155;
        }}
        .btn-clear:hover {{
            background-color: #334155;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Deployed Container Diagnostics</h1>
        
        {status_banner}

        <div class="card">
            <div class="card-title">Load Simulation Controls</div>
            <p style="font-size: 0.875rem; color: #a1a1aa; margin-bottom: 1rem;">
                Click the buttons below to generate CPU or memory utilization. Use the dashboard telemetry charts to watch these metrics live!
            </p>
            <a href="?action=cpu&duration=10" class="btn btn-cpu">🔥 Spike CPU (10s @ 100%)</a>
            <a href="?action=ram&mb=50" class="btn btn-ram">🟢 Allocate 50 MB RAM</a>
            <a href="?action=ram&mb=100" class="btn btn-ram">🟢 Allocate 100 MB RAM</a>
            <a href="?action=ram&mb=200" class="btn btn-ram">🟢 Allocate 200 MB RAM</a>
            <a href="?action=clear_ram" class="btn btn-clear">🧹 Clear Allocated RAM</a>
        </div>
        
        <div class="card">
            <div class="card-title">System & Kernel Details</div>
            <table>
                <tr>
                    <td class="label">OS Platform:</td>
                    <td class="value">{os_release.replace(chr(10), '<br>')}</td>
                </tr>
                <tr>
                    <td class="label">Kernel Release:</td>
                    <td class="value">{kernel}</td>
                </tr>
                <tr>
                    <td class="label">Python Version:</td>
                    <td class="value">{python_ver}</td>
                </tr>
            </table>
        </div>

        <div class="card">
            <div class="card-title">Network Info</div>
            <table>
                <tr>
                    <td class="label">Hostname:</td>
                    <td class="value">{hostname}</td>
                </tr>
                <tr>
                    <td class="label">Container IP:</td>
                    <td class="value">{ip_addr}</td>
                </tr>
            </table>
        </div>

        <div class="card">
            <div class="card-title">User & Permissions Context</div>
            <table>
                <tr>
                    <td class="label">Current User:</td>
                    <td class="value">{username} (UID: {uid})</td>
                </tr>
                <tr>
                    <td class="label">Group:</td>
                    <td class="value">GID: {gid}</td>
                </tr>
            </table>
        </div>

        <div class="card">
            <div class="card-title">Cgroup Memory Limits</div>
            <table>
                <tr>
                    <td class="label">Memory Limit (Bytes):</td>
                    <td class="value">{mem_limit} ({mem_limit_mb})</td>
                </tr>
                <tr>
                    <td class="label">Memory Usage (Bytes):</td>
                    <td class="value">{mem_usage} ({mem_usage_mb})</td>
                </tr>
            </table>
        </div>

        <div class="card">
            <div class="card-title">Files & Mounts</div>
            <table>
                <tr>
                    <td class="label">Working Dir:</td>
                    <td class="value">{os.getcwd()}</td>
                </tr>
                <tr>
                    <td class="label">Files in workdir:</td>
                    <td class="value">{files_str}</td>
                </tr>
                <tr>
                    <td class="label">Active Mounts (top 15):</td>
                    <td class="value">
                        <pre>{mounts_str}</pre>
                    </td>
                </tr>
            </table>
        </div>

        <div class="card">
            <div class="card-title">Injected Environment Variables</div>
            <table>
                {env_table_content}
            </table>
        </div>
    </div>
</body>
</html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

# Bind to port 8080 or port specified by PORT env var
port = int(os.environ.get("PORT", 8080))
print(f"Starting server on port {port}...")
HTTPServer(("0.0.0.0", port), Handler).serve_forever()
