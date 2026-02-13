import sys
import subprocess
from pathlib import Path

def main():
    """
    Entry point for the Streamlit UI.
    It locates the streamlit app file within the package and runs it using `streamlit run`.
    """
    # Locate the app.py file inside the installed package
    import recipe_helper.ui.app as app_module
    app_path = Path(app_module.__file__).resolve()

    # If __init__.py is returned (shouldn't happen with direct import but good safety), find app.py
    if app_path.name == "__init__.py":
        app_path = app_path.parent / "app.py"

    print(f"Starting Recipe Helper UI from: {app_path}")
    
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)] + sys.argv[1:]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error running Streamlit app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
