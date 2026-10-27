from app.db.session import SessionLocal
from app.core.deps import user_from_authorization


async def get_context_value(request, data):
    db = SessionLocal()
    request.state.graphql_db = db
    try:
        user = user_from_authorization(request.headers.get("authorization"), db)
        return {"request": request, "db": db, "user": user}
    except Exception:
        db.close()
        raise
