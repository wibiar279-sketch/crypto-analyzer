import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from src.main import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

