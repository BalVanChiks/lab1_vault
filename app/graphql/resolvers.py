import json
import uuid
from datetime import datetime

from ariadne import QueryType, MutationType, ObjectType, convert_kwargs_to_snake_case

from app.models.user import User
from app.models.client import OAuthClient
from app.models.audit import AuditEvent
from app.core.passwords import hash_password, validate_policy, WeakPasswordError
from app.core.jwt import create_access_token
from app.audit.service import write_event

query = QueryType()
mutation = MutationType()

# ============================================================
# Типы с явными резолверами полей (camelCase → snake_case)
# ============================================================

client_type = ObjectType("Client")

@client_type.field("clientId")
def resolve_client_id(client, info):
    return client.client_id

@client_type.field("isConfidential")
def resolve_is_confidential(client, info):
    return client.is_confidential

@client_type.field("redirectUris")
def resolve_redirect_uris(client, info):
    return client.redirect_uris or []

@client_type.field("createdAt")
def resolve_client_created_at(client, info):
    if isinstance(client.created_at, datetime):
        return client.created_at.isoformat()
    return str(client.created_at) if client.created_at else None


user_type = ObjectType("User")

@user_type.field("isActive")
def resolve_is_active(user, info):
    return user.is_active

@user_type.field("isAdmin")
def resolve_is_admin(user, info):
    return user.is_admin

@user_type.field("createdAt")
def resolve_user_created_at(user, info):
    if isinstance(user.created_at, datetime):
        return user.created_at.isoformat()
    return str(user.created_at) if user.created_at else None


audit_event_type = ObjectType("AuditEvent")

@audit_event_type.field("eventType")
def resolve_event_type(event, info):
    return event.event_type

@audit_event_type.field("actorId")
def resolve_actor_id(event, info):
    return event.actor_id

@audit_event_type.field("userAgent")
def resolve_user_agent(event, info):
    return event.user_agent

@audit_event_type.field("metadata")
def resolve_metadata(event, info):
    if event.metadata_json is None:
        return "{}"
    if isinstance(event.metadata_json, dict):
        return json.dumps(event.metadata_json, ensure_ascii=False)
    return str(event.metadata_json)

@audit_event_type.field("createdAt")
def resolve_audit_created_at(event, info):
    if isinstance(event.created_at, datetime):
        return event.created_at.isoformat()
    return str(event.created_at) if event.created_at else None


auth_payload_type = ObjectType("AuthPayload")

@auth_payload_type.field("accessToken")
def resolve_access_token(payload, info):
    return payload.get("accessToken", "")

@auth_payload_type.field("tokenType")
def resolve_token_type(payload, info):
    return payload.get("tokenType", "bearer")


# ============================================================
# Query резолверы
# ============================================================

@query.field("me")
def resolve_me(_, info):
    user = info.context.get("user")
    if not user:
        raise Exception("Authentication required")
    return user


@query.field("users")
@convert_kwargs_to_snake_case
def resolve_users(_, info, search=None, limit=10, offset=0):
    db = info.context["db"]
    q = db.query(User)
    if search:
        q = q.filter(User.email.ilike(f"%{search}%"))
    return q.offset(offset).limit(limit).all()


@query.field("clients")
def resolve_clients(_, info):
    db = info.context["db"]
    return db.query(OAuthClient).all()


@query.field("auditEvents")
@convert_kwargs_to_snake_case
def resolve_audit_events(_, info, event_type=None, limit=20, offset=0):
    db = info.context["db"]
    q = db.query(AuditEvent)
    if event_type:
        q = q.filter(AuditEvent.event_type == event_type)
    return q.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()


# ============================================================
# Mutation резолверы
# ============================================================

@mutation.field("registerUser")
@convert_kwargs_to_snake_case
def resolve_register_user(_, info, email, password):
    db = info.context["db"]
    request = info.context["request"]

    if db.query(User).filter(User.email == email).first():
        raise Exception("Email already registered")

    try:
        validate_policy(password, user_inputs=[email])
    except WeakPasswordError as e:
        raise Exception(str(e))

    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    write_event(
        db,
        "user.created",
        actor_id=user.id,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    token = create_access_token(sub=user.email)
    return {"accessToken": token, "tokenType": "bearer"}


@mutation.field("createClient")
@convert_kwargs_to_snake_case
def resolve_create_client(_, info, name, is_confidential):
    db = info.context["db"]
    request = info.context["request"]
    user = info.context["user"]

    if not user:
        raise Exception("Authentication required")
    if not user.is_admin:
        raise Exception("Admin only")

    client = OAuthClient(
        client_id=str(uuid.uuid4()),
        name=name,
        is_confidential=is_confidential,
        redirect_uris=[],
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    write_event(
        db,
        "client.created",
        actor_id=user.id,
        client_id=client.client_id,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    return client


@mutation.field("disableUser")
@convert_kwargs_to_snake_case
def resolve_disable_user(_, info, user_id):
    db = info.context["db"]
    request = info.context["request"]
    actor = info.context["user"]

    if not actor:
        raise Exception("Authentication required")
    if not actor.is_admin:
        raise Exception("Admin only")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise Exception("User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)

    write_event(
        db,
        "user.disabled",
        actor_id=actor.id,
        metadata={"target_user_id": user_id},
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    return user