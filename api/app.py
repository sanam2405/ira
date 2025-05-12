from typing import Literal

from fastapi import FastAPI

app = FastAPI()


@app.get("/health", description="Check the health of the API service")
def health() -> Literal["IRA"]:
    return "IRA"
