from enum import Enum


class UserRole(str, Enum):
    CLIENT = "client"
    WORKER = "worker"
    ADMIN = "admin"
