from fastapi import FastAPI

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/")
def home():
    return {"message": "Welcome to the analytics dashboard!"}