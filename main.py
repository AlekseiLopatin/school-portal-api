from fastapi import FastAPI

app = FastAPI(title="School Portal API")


@app.get("/")
async def root():
    return {"message": "School Portal API is running"}


@app.get("/health")
async def health_check():
    return {"status": "Ok"}