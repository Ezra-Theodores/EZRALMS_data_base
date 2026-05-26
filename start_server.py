#!/usr/bin/env python3
"""
Simple script to start the EZRA LMS Flask server
Handles imports gracefully and starts the app
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to install missing packages if needed
try:
    import flask
except ImportError:
    print("Installing Flask...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "python-dotenv", "-q"])

# Now import and run the app
if __name__ == '__main__':
    # Change to the app directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Import the Flask app
    from unified_app import app

    # Run the Flask app
    port = int(os.getenv("UNIFIED_PORT", "5000"))
    print("Starting EZRA LMS...")
    print(f"Open browser to: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
