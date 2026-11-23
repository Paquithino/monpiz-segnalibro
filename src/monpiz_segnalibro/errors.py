"""Errors shown to the user as plain messages, without a traceback."""


class ContentError(Exception):
    """The content (YAML, images, fonts) cannot produce a bookmark."""
