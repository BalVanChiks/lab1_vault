from ariadne import SchemaDirectiveVisitor
from graphql import default_field_resolver


class IsAuthenticatedDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original_resolver = field.resolve or default_field_resolver

        def resolve_auth(obj, info, **kwargs):
            if not info.context.get("user"):
                raise Exception("Authentication required")
            return original_resolver(obj, info, **kwargs)

        field.resolve = resolve_auth
        return field


class IsAdminDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original_resolver = field.resolve or default_field_resolver

        def resolve_admin(obj, info, **kwargs):
            user = info.context.get("user")
            if not user:
                raise Exception("Authentication required")
            if not user.is_admin:
                raise Exception("Admin only")
            return original_resolver(obj, info, **kwargs)

        field.resolve = resolve_admin
        return field