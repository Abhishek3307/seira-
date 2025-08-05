# app.py

from flask import Flask, render_template, request, jsonify
import os
import sys

# Ensure the project root is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the PipelineRunner (assuming it's relative to the project root)
try:
    from pipeline_runner.main import PipelineRunner
    print("Successfully imported PipelineRunner into app.py.")
except ImportError as e:
    print(f"Error importing PipelineRunner in app.py: {e}")
    print("Please ensure 'pipeline_runner' folder exists and 'main.py' is inside it.")
    sys.exit(1)

app = Flask(__name__)

# Initialize PipelineRunner
# We initialize it once when the app starts.
# Note: For production, you might want a more robust way to manage instances.
pipeline_runner = PipelineRunner()

@app.route('/')
def index():
    """
    Renders the main index page.
    """
    return render_template('index.html')

@app.route('/run_devika', methods=['POST'])
def run_devika():
    """
    Endpoint to receive user prompt and run the Devika pipeline.
    """
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({'status': 'error', 'message': 'No prompt provided'}), 400

    # In a real-time scenario, you'd run this in a background thread/process
    # to avoid blocking the web server. For now, we'll run it directly.
    print(f"Received prompt: '{user_prompt}'. Running Devika pipeline...")
    
    # We will capture the output later. For now, it will print to the console
    # where Gunicorn/Flask is running.
    # TODO: Implement a way to capture and stream pipeline output to the frontend.
    pipeline_runner.run_pipeline(user_prompt) 

    return jsonify({'status': 'success', 'message': 'Devika pipeline started. Check server console for output.'})

if __name__ == '__main__':
    # For local development, you can run with: python app.py
    # For production, use Gunicorn: gunicorn -w 4 app:app
    print("Starting Flask app...")
    app.run(debug=True, port=5000)