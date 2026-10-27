from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.graphql.schema import graphql_app
from app.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(auth_router)
app.mount("/graphql", graphql_app)
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/")
def read_root():
    return {"message": "Welcome to Vault API. Visit /docs for REST or /graphql for GraphQL."}