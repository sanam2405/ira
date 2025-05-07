from fastapi import FastAPI
from typing import Literal
app = FastAPI()


@app.get("/health", description="Check the health of the API service")
def health() -> Literal["IRA"]:
    return "IRA"

