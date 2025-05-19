import os
import sys
import subprocess
import time

# Debug files to check
DEBUG_FILES = ["logs"]

def clear_debug_files():
    """Clear existing debug files"""
    print("Clearing existing debug files...")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("  - Created logs directory")
    else:
        # Clear log files but keep the directory
        for file in os.listdir("logs"):
            try:
                os.remove(os.path.join("logs", file))
                print(f"  - Removed log file: {file}")
            except Exception as e:
                print(f"  - Failed to remove {os.path.join('logs', file)}: {str(e)}")

def run_main_app():
    """Run the main application"""
    print("\nStarting main application...")
    
    try:
        # Run main.py with our Python interpreter
        cmd = [sys.executable, "main.py"]
        proc = subprocess.Popen(cmd)
        
        # Wait for a few seconds to give it time to initialize
        print("Waiting for application to initialize (10 seconds)...")
        for i in range(10):
            time.sleep(1)
            # Check if logs directory has any files
            if os.path.exists("logs") and os.listdir("logs"):
                print(f"\nLOG FILES FOUND after {i+1} seconds!")
                for file in os.listdir("logs"):
                    full_path = os.path.join("logs", file)
                    if os.path.isfile(full_path):
                        size = os.path.getsize(full_path)
                        print(f"  - {file} ({size} bytes)")
            else:
                print(".", end="", flush=True)
        
        print("\nSimulating user interaction (sending message)...")
        # We need to interact with the app, but can't easily do this programmatically
        # So just wait longer to give the user time to click on the AI chat and send a message
        for i in range(30):
            time.sleep(1)
            print(".", end="", flush=True)
            
            # Check log files every few seconds
            if i % 5 == 0 and os.path.exists("logs") and os.listdir("logs"):
                print("\nLog files update:")
                for file in os.listdir("logs"):
                    full_path = os.path.join("logs", file)
                    if os.path.isfile(full_path):
                        size = os.path.getsize(full_path)
                        print(f"  - {file} ({size} bytes)")
        
        print("\nSending termination signal...")
        
        # Try to terminate gracefully
        proc.terminate()
        
        # Wait for process to end
        print("Waiting for application to terminate...")
        proc.wait(timeout=5)
        print("Application terminated.")
    except Exception as e:
        print(f"Error running main application: {str(e)}")

def check_debug_files():
    """Check for and display debug files"""
    print("\nChecking for log files...")
    
    # Check logs directory
    if os.path.exists("logs"):
        print("\nContents of logs directory:")
        files = os.listdir("logs")
        for file in files:
            full_path = os.path.join("logs", file)
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                print(f"  - {file} ({size} bytes)")
                
                # For smallish log files, show content
                if size < 10000 and file.endswith(".log"):
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            print("-" * 50)
                            print(content[:1000] + ("..." if len(content) > 1000 else ""))
                            print("-" * 50)
                    except Exception as e:
                        print(f"    Error reading file: {str(e)}")

def main():
    """Main function"""
    print("=== DEBUG TEST FOR VPYCODE ===")
    
    # Clear existing debug files
    clear_debug_files()
    
    # Run the application
    run_main_app()
    
    # Check debug files
    check_debug_files()
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    main() 