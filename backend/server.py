# Compatibility wrapper for Nutri-RAG Modular
# Use 'main.py' for the updated version

if __name__ == "__main__":
    import uvicorn
    # Importing from the new main entry point
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8000)
