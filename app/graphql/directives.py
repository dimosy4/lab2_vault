from ariadne import SchemaDirectiveVisitor
from graphql import default_field_resolver, GraphQLError


class IsAuthenticatedDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original = field.resolve or default_field_resolver

        def protected(obj, info, **kwargs):
            if info.context.get("user") is None:
                raise GraphQLError("Authentication required")
            return original(obj, info, **kwargs)
        field.resolve = protected
        return field


class IsAdminDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original = field.resolve or default_field_resolver

        def protected(obj, info, **kwargs):
            user = info.context.get("user")
            if user is None or not user.is_admin:
                raise GraphQLError("Admin only")
            return original(obj, info, **kwargs)
        field.resolve = protected
        return field
