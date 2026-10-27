from uuid import uuid4
from ariadne import QueryType, MutationType, ObjectType, ScalarType, convert_kwargs_to_snake_case
from graphql import GraphQLError
from sqlalchemy import select
from app.models import User, OAuthClient, AuditEvent
from app.core.passwords import validate_policy, hash_password, WeakPasswordError
from app.core.jwt import create_access_token
from app.audit.service import write_event

query = QueryType()
mutation = MutationType()
user_type = ObjectType("User")
client_type = ObjectType("Client")
audit_type = ObjectType("AuditEvent")
json_scalar = ScalarType("JSON")


@json_scalar.serializer
def serialize_json(value):
    return value


def scalar(obj, field):
    value = getattr(obj, field)
    return value.isoformat() if hasattr(value, "isoformat") else value


for obj_type, mapping in [
    (user_type, {"isActive": "is_active", "isAdmin": "is_admin", "createdAt": "created_at"}),
    (client_type, {"clientId": "client_id", "isConfidential": "is_confidential", "redirectUris": "redirect_uris", "createdAt": "created_at"}),
    (audit_type, {"eventType": "event_type", "actorId": "actor_id", "userAgent": "user_agent", "metadata": "metadata_json", "createdAt": "created_at"}),
]:
    for graphql_name, python_name in mapping.items():
        obj_type.set_field(graphql_name, lambda obj, info, attr=python_name: scalar(obj, attr))


@query.field("me")
def resolve_me(_, info):
    return info.context["user"]


@query.field("users")
def resolve_users(_, info, search=None, limit=50, offset=0):
    stmt = select(User).order_by(User.id)
    if search:
        stmt = stmt.where(User.email.ilike(f"%{search}%"))
    return info.context["db"].scalars(stmt.offset(max(offset, 0)).limit(min(max(limit, 0), 100))).all()


@query.field("clients")
def resolve_clients(_, info):
    return info.context["db"].scalars(select(OAuthClient).order_by(OAuthClient.id)).all()


@query.field("auditEvents")
@convert_kwargs_to_snake_case
def resolve_audit(_, info, event_type=None, limit=50, offset=0):
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    return info.context["db"].scalars(stmt.offset(max(offset, 0)).limit(min(max(limit, 0), 100))).all()


@mutation.field("registerUser")
def resolve_register(_, info, email, password):
    db = info.context["db"]
    email = email.strip().lower()
    if "@" not in email:
        raise GraphQLError("Invalid email")
    if db.scalar(select(User).where(User.email == email)):
        raise GraphQLError("Email already registered")
    try:
        validate_policy(password, [email])
    except WeakPasswordError as exc:
        raise GraphQLError(str(exc)) from exc
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.flush()
    write_event(db, "user.created", actor_id=user.id, commit=False)
    db.commit()
    return {"accessToken": create_access_token(email), "tokenType": "bearer"}


@mutation.field("createClient")
@convert_kwargs_to_snake_case
def resolve_create_client(_, info, name, is_confidential):
    db = info.context["db"]
    if not name.strip():
        raise GraphQLError("Client name is required")
    client = OAuthClient(name=name.strip(), is_confidential=is_confidential,
                         client_id=uuid4().hex, redirect_uris=[])
    db.add(client)
    db.flush()
    request = info.context["request"]
    write_event(db, "client.created", actor_id=info.context["user"].id,
                client_id=client.client_id, ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"), commit=False)
    db.commit()
    return client


@mutation.field("disableUser")
@convert_kwargs_to_snake_case
def resolve_disable_user(_, info, user_id):
    db = info.context["db"]
    user = db.get(User, int(user_id))
    if user is None:
        raise GraphQLError("User not found")
    if user.id == info.context["user"].id:
        raise GraphQLError("You cannot disable yourself")
    user.is_active = False
    write_event(db, "user.disabled", actor_id=info.context["user"].id,
                metadata={"target_user_id": user.id}, commit=False)
    db.commit()
    return user
