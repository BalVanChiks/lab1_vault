from ariadne import (
    load_schema_from_path,
    make_executable_schema,
    snake_case_fallback_resolvers,
)
from ariadne.asgi import GraphQL

from app.graphql.resolvers import (
    query,
    mutation,
    client_type,
    user_type,
    audit_event_type,
    auth_payload_type,
)
from app.graphql.context import get_context_value
from app.graphql.directives import IsAuthenticatedDirective, IsAdminDirective

# Загружаем SDL-схему из файла
type_defs = load_schema_from_path("app/graphql/schema.graphql")

# Собираем исполняемую схему
schema = make_executable_schema(
    type_defs,
    query,
    mutation,
    snake_case_fallback_resolvers,  # автоматическое преобразование camelCase → snake_case
    client_type,                    # явные резолверы для типа Client
    user_type,                      # явные резолверы для типа User
    audit_event_type,               # явные резолверы для типа AuditEvent
    auth_payload_type,              # явные резолверы для типа AuthPayload
    directives={
        "isAuthenticated": IsAuthenticatedDirective,
        "isAdmin": IsAdminDirective,
    },
)

# ASGI-приложение для GraphQL
graphql_app = GraphQL(schema, context_value=get_context_value, debug=True)