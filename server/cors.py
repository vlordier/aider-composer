from flask import Flask, Response


class CORS:
    """This class is used to add CORS headers to the response."""

    def __init__(self, app: Flask = None) -> None:
        self.app = app
        self.init_app(app)

    def init_app(self, app: Flask) -> None:
        app.after_request(self.add_cors_headers)

    def add_cors_headers(self, response: Response) -> Response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers[
            "Access-Control-Allow-Methods"
        ] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
