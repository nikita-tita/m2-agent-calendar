from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="M² Agent Calendar")

@app.get("/health")
def health():
    return {"status": "healthy", "version": "simple"}

@app.get("/")
def root():
    return {"app": "M² Agent Calendar", "status": "running"}

@app.get("/api/v1/miniapp/", response_class=HTMLResponse)
def miniapp():
    return '''
    <!DOCTYPE html>
    <html><head><title>M² Calendar</title></head>
    <body style="font-family: Arial; padding: 20px; background: linear-gradient(45deg, #667eea, #764ba2); color: white;">
        <h1>🏢 M² Agent Calendar</h1>
        <h2>✅ Система работает!</h2>
        <p>Mini App готов к использованию</p>
        <p>Bot Token: 7794113902:AAH...</p>
    </body></html>
    '''

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
