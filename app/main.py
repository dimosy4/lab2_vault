from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.auth.router import router as auth_router
from app.graphql.schema import graphql_app

app = FastAPI(title=settings.app_name)
app.include_router(auth_router)
app.mount("/graphql", graphql_app)
app.mount("/admin", StaticFiles(directory=str(Path(__file__).with_name("static")), html=True), name="admin")


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/admin/")


@app.get("/health")
def health():
    return {"status": "ok"}


class GraphQLSessionCleanup:
    """ASGI middleware: close GraphQL DB session after full HTTP response."""
    def __init__(self, app):
        self.asgi_app = app

    async def __call__(self, scope, receive, send):
        try:
            await self.asgi_app(scope, receive, send)
        finally:
            db = scope.get("state", {}).get("graphql_db")
            if db is not None:
                db.close()


app.add_middleware(GraphQLSessionCleanup)
