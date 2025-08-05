"""
    DO NOT REARRANGE THE ORDER OF THE FUNCTION CALLS AND VARIABLE DECLARATIONS
    AS IT MAY CAUSE IMPORT ERRORS AND OTHER ISSUES
"""
from gevent import monkey
monkey.patch_all()
from src.init import init_devika
init_devika()


from flask import Flask, request, jsonify, send_file, send_from_directory, render_template_string
from flask_cors import CORS
from src.socket_instance import socketio, emit_agent
import os
import logging
from threading import Thread
import tiktoken

from src.apis.project import project_bp
from src.config import Config
from src.logger import Logger, route_logger
from src.project import ProjectManager
from src.state import AgentState
from src.agents import Agent
from src.llm import LLM


app = Flask(__name__)
# Change the origin to your frontend URL
CORS(app, resources={r"/*": {"origins": [
                                 "https://localhost:3000",
                                 "http://localhost:3000",
                                 ]}})
app.register_blueprint(project_bp)
socketio.init_app(app)


log = logging.getLogger("werkzeug")
log.disabled = True


TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")

os.environ["TOKENIZERS_PARALLELISM"] = "false"

manager = ProjectManager()
agent_state = AgentState()
config = Config()
logger = Logger()


# Root route to serve main UI
@app.route("/")
def index():
    """Serve the main Devika AI interface"""
    # Simple HTML page with Devika AI interface
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Devika AI - AI Software Engineer</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: bold;
            }
            input, select, textarea {
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.9);
                color: #333;
                font-size: 16px;
                box-sizing: border-box;
            }
            textarea {
                height: 120px;
                resize: vertical;
            }
            button {
                background: #4CAF50;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 18px;
                width: 100%;
                transition: background 0.3s;
            }
            button:hover {
                background: #45a049;
            }
            .status {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                display: none;
            }
            .api-info {
                background: rgba(0, 0, 0, 0.2);
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Devika AI</h1>
            <div class="api-info">
                <h3>AI Software Engineer</h3>
                <p>Enter a prompt below to have Devika generate code for you.</p>
                <p><strong>Available Models:</strong> phi:latest (Ollama Local LLM)</p>
            </div>
            
            <form id="devikaForm">
                <div class="form-group">
                    <label for="project_name">Project Name:</label>
                    <input type="text" id="project_name" name="project_name" placeholder="my-awesome-project" required>
                </div>
                
                <div class="form-group">
                    <label for="base_model">Model:</label>
                    <select id="base_model" name="base_model" required>
                        <option value="phi:latest">phi:latest (Ollama)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="search_engine">Search Engine:</label>
                    <select id="search_engine" name="search_engine" required>
                        <option value="google">Google</option>
                        <option value="bing">Bing</option>
                        <option value="duckduckgo">DuckDuckGo</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="message">Task Description:</label>
                    <textarea id="message" name="message" placeholder="Create a simple to-do list web application with HTML, CSS, and JavaScript..." required></textarea>
                </div>
                
                <button type="submit">🚀 Generate Code</button>
            </form>
            
            <div id="status" class="status">
                <h3>Status:</h3>
                <p id="statusText">Ready to generate code...</p>
            </div>
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            const form = document.getElementById('devikaForm');
            const status = document.getElementById('status');
            const statusText = document.getElementById('statusText');
            
            socket.on('connect', function() {
                console.log('Connected to Devika AI');
                statusText.textContent = 'Connected to Devika AI - Ready!';
                status.style.display = 'block';
            });
            
            socket.on('info', function(data) {
                statusText.textContent = data.message || 'Processing...';
                status.style.display = 'block';
            });
            
            socket.on('logs', function(data) {
                statusText.textContent = data.message || 'Working on your task...';
                status.style.display = 'block';
            });
            
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(form);
                const data = {
                    message: formData.get('message'),
                    base_model: formData.get('base_model'),
                    project_name: formData.get('project_name'),
                    search_engine: formData.get('search_engine')
                };
                
                statusText.textContent = 'Sending task to Devika AI...';
                status.style.display = 'block';
                
                socket.emit('user-message', data);
            });
        </script>
    </body>
    </html>
    """
    return html_content

# initial socket
@socketio.on('socket_connect')
def test_connect(data):
    print("Socket connected :: ", data)
    emit_agent("socket_response", {"data": "Server Connected"})


@app.route("/api/data", methods=["GET"])
@route_logger(logger)
def data():
    project = manager.get_project_list()
    models = LLM().list_models()
    search_engines = ["Bing", "Google", "DuckDuckGo"]
    return jsonify({"projects": project, "models": models, "search_engines": search_engines})


@app.route("/api/messages", methods=["POST"])
def get_messages():
    data = request.json
    project_name = data.get("project_name")
    messages = manager.get_messages(project_name)
    return jsonify({"messages": messages})


# Main socket
@socketio.on('user-message')
def handle_message(data):
    logger.info(f"User message: {data}")
    message = data.get('message')
    base_model = data.get('base_model')
    project_name = data.get('project_name')
    search_engine = data.get('search_engine').lower()

    agent = Agent(base_model=base_model, search_engine=search_engine)

    state = agent_state.get_latest_state(project_name)
    if not state:
        thread = Thread(target=lambda: agent.execute(message, project_name))
        thread.start()
    else:
        if agent_state.is_agent_completed(project_name):
            thread = Thread(target=lambda: agent.subsequent_execute(message, project_name))
            thread.start()
        else:
            emit_agent("info", {"type": "warning", "message": "previous agent doesn't completed it's task."})
            last_state = agent_state.get_latest_state(project_name)
            if last_state and (last_state.get("agent_is_active") or not last_state.get("completed")):
                thread = Thread(target=lambda: agent.execute(message, project_name))
                thread.start()
            else:
                thread = Thread(target=lambda: agent.subsequent_execute(message, project_name))
                thread.start()

@app.route("/api/is-agent-active", methods=["POST"])
@route_logger(logger)
def is_agent_active():
    data = request.json
    project_name = data.get("project_name")
    is_active = agent_state.is_agent_active(project_name)
    return jsonify({"is_active": is_active})


@app.route("/api/get-agent-state", methods=["POST"])
@route_logger(logger)
def get_agent_state():
    data = request.json
    project_name = data.get("project_name")
    latest_state = agent_state.get_latest_state(project_name)
    return jsonify({"state": latest_state})


@app.route("/api/get-browser-snapshot", methods=["GET"])
@route_logger(logger)
def browser_snapshot():
    snapshot_path = request.args.get("snapshot_path")
    return send_file(snapshot_path, as_attachment=True)


@app.route("/api/get-browser-session", methods=["GET"])
@route_logger(logger)
def get_browser_session():
    project_name = request.args.get("project_name")
    latest_state = agent_state.get_latest_state(project_name)
    if not latest_state:
        return jsonify({"session": None})
    else:
        browser_session = latest_state.get("browser_session")
        return jsonify({"session": browser_session})


@app.route("/api/get-terminal-session", methods=["GET"])
@route_logger(logger)
def get_terminal_session():
    project_name = request.args.get("project_name")
    latest_state = agent_state.get_latest_state(project_name)
    if not latest_state:
        return jsonify({"terminal_state": None})
    else:
        terminal_state = latest_state.get("terminal_session")
        return jsonify({"terminal_state": terminal_state})


@app.route("/api/run-code", methods=["POST"])
@route_logger(logger)
def run_code():
    data = request.json
    project_name = data.get("project_name")
    code = data.get("code")
    # TODO: Implement code execution logic
    return jsonify({"message": "Code execution started"})


@app.route("/api/calculate-tokens", methods=["POST"])
@route_logger(logger)
def calculate_tokens():
    data = request.json
    prompt = data.get("prompt")
    tokens = len(TIKTOKEN_ENC.encode(prompt))
    return jsonify({"token_usage": tokens})


@app.route("/api/token-usage", methods=["GET"])
@route_logger(logger)
def token_usage():
    project_name = request.args.get("project_name")
    token_count = agent_state.get_latest_token_usage(project_name)
    return jsonify({"token_usage": token_count})


@app.route("/api/logs", methods=["GET"])
def real_time_logs():
    log_file = logger.read_log_file()
    return jsonify({"logs": log_file})


@app.route("/api/settings", methods=["POST"])
@route_logger(logger)
def set_settings():
    data = request.json
    config.update_config(data)
    return jsonify({"message": "Settings updated"})


@app.route("/api/settings", methods=["GET"])
@route_logger(logger)
def get_settings():
    configs = config.get_config()
    return jsonify({"settings": configs})


@app.route("/api/status", methods=["GET"])
@route_logger(logger)
def status():
    return jsonify({"status": "server is running!"})

if __name__ == "__main__":
    # Initialize and start PipelineRunner
    try:
        from pipeline_runner.main import PipelineRunner
        pipeline = PipelineRunner()
        logger.info("PipelineRunner initialized successfully!")
        logger.info(f"Available LLM models: {pipeline.llm_connector.get_available_models()}")
    except Exception as e:
        logger.error(f"Failed to initialize PipelineRunner: {e}")
        logger.info("Continuing without PipelineRunner...")
    
    logger.info("Devika is up and running!")
    socketio.run(app, debug=False, port=1337, host="0.0.0.0")