import enum

class UserType(enum.Enum):
    Admin = 1
    User = 2
    Guest = 3

class UserConnectMethod(enum.Enum):
    Site = 'site'
    Google = 'google'
    GitHub = 'github'
    Facebook = 'fb'
    