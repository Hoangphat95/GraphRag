class SchemaChecker:

    def __init__(self, schema):
        self.schema = schema

    def is_valid_property(self, prop):
        for props in self.schema["properties"].values():
            if prop in props:
                return True
        return False