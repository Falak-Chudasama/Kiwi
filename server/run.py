import uvicorn
import os

if __name__ == "__main__":
    host = os.environ.get("KIWI_HOST", "127.0.0.3")
    port = int(os.environ.get("KIWI_PORT", "10000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
