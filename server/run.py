import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.4", port=5060, reload=False)
