# Local imports
from StorageServer import create_app


# Create the app instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
