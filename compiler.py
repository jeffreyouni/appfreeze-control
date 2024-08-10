import subprocess
import sys

params = [
    sys.executable, "-m", "PyInstaller",
    "--name", "AppFreeze Control",
    "--onefile",
    "--windowed",
    "--add-data", "pssuspend.exe;.",
    "main.py"
]


def install_package(package):
    """Install a package using pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def generate_requirements():
    """Generate requirements.txt file."""
    try:
        with open('requirements.txt', 'w') as f:
            subprocess.check_call([sys.executable, '-m', 'pip', 'freeze'], stdout=f)
        print("requirements.txt generated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    try:
        # Check if PyInstaller is installed
        __import__('PyInstaller')
    except ImportError:
        print("PyInstaller is not installed. Installing PyInstaller...")
        install_package('pyinstaller')
    else:
        print("PyInstaller is already installed.")

    # Run the PyInstaller command to create a standalone executable
    print("Creating standalone executable...")
    subprocess.check_call(params)
    print("Standalone executable created successfully.")


if __name__ == "__main__":
    # Generate requirements.txt before creating the standalone executable
    generate_requirements()
    main()