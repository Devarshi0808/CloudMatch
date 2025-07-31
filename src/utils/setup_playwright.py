#!/usr/bin/env python3
"""
Setup script to install Playwright browsers for headless scraping
"""

import subprocess
import sys

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("🔧 Installing Playwright browsers...")
    
    try:
        # Install Playwright browsers
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully!")
            print("You can now run the GCP headless scraping scripts.")
        else:
            print("❌ Failed to install Playwright browsers:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error installing Playwright browsers: {e}")

def check_playwright_installation():
    """Check if Playwright is properly installed"""
    print("🔍 Checking Playwright installation...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "playwright", "--version"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Playwright is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Playwright is not installed or not working properly")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Playwright: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Playwright Setup for GCP Marketplace Scraping")
    print("=" * 50)
    
    # Check if Playwright is installed
    if check_playwright_installation():
        # Install browsers
        install_playwright_browsers()
    else:
        print("\n📦 Please install Playwright first:")
        print("pip install playwright")
        print("\nThen run this script again to install browsers.") 