from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramAPIServer:
    """
    Base config for API Endpoints
    """

    base: str
    file: str

    def api_url(self, token: str, method: str) -> str:
        """
        Generate URL for API methods
        :param token: Bot token
        :param method: API method name (case insensitive)
        :return: URL
        """
        return self.base.format(token=token, method=method)

    def file_url(self, token: str, path: str) -> str:
        """
        Generate URL for downloading files
        :param token: Bot token
        :param path: file path
        :return: URL
        """
        return self.file.format(token=token, path=path)

    @classmethod
    def from_base(cls, base: str) -> 'TelegramAPIServer':
        base = base.rstrip("/")
        return cls(
            base=f"{base}/bot{{token}}/test/{{method}}",
            file=f"{base}/file/bot{{token}}/{{path}}",
        )


TELEGRAM_TEST = TelegramAPIServer.from_base("https://api.telegram.org")