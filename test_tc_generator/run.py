import subprocess
import sys
import os

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import streamlit
        import langchain
        import pandas
        import openpyxl
        print("✅ All core dependencies are installed.")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required packages from requirements.txt"""
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed successfully.")

def generate_template():
    """Generate the testcase template"""
    from templates.testcase_template import create_testcase_template
    template_path = os.path.join('templates', 'testcase_template.xlsx')
    create_testcase_template(template_path)
    print(f"✅ Template created at: {template_path}")

def run_app():
    """Run the Streamlit app"""
    print("🚀 Starting the application...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/app.py"])

if __name__ == "__main__":
    print("🔍 Checking dependencies...")
    
    if not check_dependencies():
        print("⚙️ Installing required dependencies...")
        install_dependencies()
    
    # Generate template if it doesn't exist
    template_path = os.path.join('templates', 'testcase_template.xlsx')
    if not os.path.exists(template_path):
        try:
            generate_template()
        except Exception as e:
            print(f"⚠️ Warning: Failed to generate template: {e}")
            print("The application will still run, but you may want to create a template manually.")
    
    # Run the application
    run_app()