# Use with enum-like classes to get from a field value to a field name.
def get_field_name(obj, value):
    # CircuitPython doesn't provide `vars` so we use `dir` and `getattr` instead.
    return next(attr for attr in dir(obj) if getattr(obj, attr) == value)
