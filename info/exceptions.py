#info/exceptions.py
"""
Custom exceptions for the Info app
"""

class InfoAppException(Exception):
    """Base exception for Info app"""
    pass


class APIServiceException(InfoAppException):
    """Raised when external API call fails"""
    def __init__(self, service_name, message, status_code=None):
        self.service_name = service_name
        self.status_code = status_code
        super().__init__(f"[{service_name}] {message}")


class WikipediaAPIException(APIServiceException):
    """Wikipedia API specific exception"""
    def __init__(self, message, status_code=None):
        super().__init__("Wikipedia", message, status_code)


class DogAPIException(APIServiceException):
    """The Dog API specific exception"""
    def __init__(self, message, status_code=None):
        super().__init__("TheDogAPI", message, status_code)


class CatAPIException(APIServiceException):
    """The Cat API specific exception"""
    def __init__(self, message, status_code=None):
        super().__init__("TheCatAPI", message, status_code)


class YouTubeAPIException(APIServiceException):
    """YouTube API specific exception"""
    def __init__(self, message, status_code=None):
        super().__init__("YouTube", message, status_code)


class BreedNotFoundException(InfoAppException):
    """Raised when breed is not found in any API"""
    def __init__(self, breed_name, species=None):
        self.breed_name = breed_name
        self.species = species
        message = f"Breed '{breed_name}' not found"
        if species:
            message += f" for species '{species}'"
        super().__init__(message)


class InvalidSpeciesException(InfoAppException):
    """Raised when invalid species is provided"""
    def __init__(self, species):
        self.species = species
        super().__init__(f"Invalid species: '{species}'")


class RateLimitException(InfoAppException):
    """Raised when API rate limit is hit"""
    def __init__(self, service_name, retry_after=None):
        self.service_name = service_name
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {service_name}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)