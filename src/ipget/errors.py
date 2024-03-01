class ConfigurationError(KeyError):
    """Exception raised for configuration errors.

    Attributes:
        missing_env_var (str): The name of the missing environment variable.
    """

    def __init__(self, missing_env_var: str) -> None:
        self.env_var: str = missing_env_var

    def __str__(self) -> str:
        return f"Missing or invalid environment variable(s): {self.env_var}"


class IPRetrievalError(Exception):
    """Exception raised when there is a failure to retrieve an IP address
    from the given URLs.

    Attributes:
        urls (list[str]): The list of URLs that were attempted to retrieve
        the IP address from.
    """

    def __init__(self, urls: list[str]) -> None:
        self.urls: list[str] = urls

    def __str__(self) -> str:
        return (
            "Failed to retrieve IP address from any of the following URLs: "
            f"{", ".join(self.urls)}"
        )
