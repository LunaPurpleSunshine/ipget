class ConfigurationError(KeyError):
    """Invalid configuration."""

    def __init__(self, missing_env_var: str) -> None:
        self.env_var: str = missing_env_var

    def __str__(self) -> str:
        return f"Missing or invalid environment variable(s): {self.env_var}"
