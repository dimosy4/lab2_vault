from pathlib import Path
from ariadne import make_executable_schema, load_schema_from_path
from ariadne.asgi import GraphQL
from app.config import settings
from app.graphql.resolvers import query, mutation, user_type, client_type, audit_type, json_scalar
from app.graphql.directives import IsAuthenticatedDirective, IsAdminDirective
from app.graphql.context import get_context_value

schema = make_executable_schema(
    load_schema_from_path(str(Path(__file__).with_name("schema.graphql"))),
    query, mutation, user_type, client_type, audit_type, json_scalar,
    directives={"isAuthenticated": IsAuthenticatedDirective, "isAdmin": IsAdminDirective},
)

# The context owns its database session; close it when the GraphQL response is finished.
class VaultGraphQL(GraphQL):
    async def __call__(self, scope, receive, send):
        # Hand off session management to a custom context callable below.
        return await super().__call__(scope, receive, send)

graphql_app = VaultGraphQL(schema, context_value=get_context_value, debug=settings.environment == "development")
