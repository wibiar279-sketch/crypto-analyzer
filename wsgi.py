import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from src.main import app

# This is the WSGI application object that Gunicorn will use
# No need to call app.run() here - Gunicorn handles that

if __name__ == "__main__":
    # Only for local testing, not used in production
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

