#!/usr/bin/env python3
"""
Main entry point for the Marketplace Matcher application
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Run the Streamlit app
    import subprocess
    import sys
    
    # Change to src directory and run streamlit
    os.chdir('src')
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py']) 