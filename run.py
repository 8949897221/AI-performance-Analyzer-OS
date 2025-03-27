import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup the environment for running NeuraPulse"""
    try:
        # Create necessary directories
        Path('logs').mkdir(exist_ok=True)
        Path('models').mkdir(exist_ok=True)
        Path('data').mkdir(exist_ok=True)
        
        # Install requirements if not already installed
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        print("Environment setup completed successfully")
        
    except Exception as e:
        print(f"Error setting up environment: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point for running NeuraPulse"""
    try:
        # Setup environment
        setup_environment()
        
        # Add src directory to Python path
        src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
        sys.path.insert(0, src_path)
        
        # Import and run main
        from src.main import main as run_neurapulse
        run_neurapulse()
        
    except Exception as e:
        print(f"Error running NeuraPulse: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 