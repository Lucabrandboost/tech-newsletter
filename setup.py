import subprocess
import sys

def setup_environment():
    print("Setting up newsletter environment...")
    
    # Install required packages
    packages = [
        'requests',
        'beautifulsoup4',
        'python-dotenv',
        'schedule',
        'flask',
        'nltk',
        'spacy'
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Download spaCy model
    print("Downloading spaCy model...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    
    print("Setup complete!")

if __name__ == "__main__":
    setup_environment() 