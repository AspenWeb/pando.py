class LoadError(StandardError):
    """Represent a problem loading a resource.
    """
    # Define this here to avoid import issues when json doesn't exist.
