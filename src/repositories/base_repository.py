"""
Repository Pattern Data Access Layer.
"""
from database.connection import db_manager

class BaseRepository:
    """Base repository with direct access to thread-safe database manager."""
    def __init__(self):
        self.db = db_manager
