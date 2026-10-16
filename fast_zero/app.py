from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from fast_zero.schemas import Message

app = FastAPI()


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Hello world!'}


@app.get(
    '/exercicio-html', status_code=HTTPStatus.OK, response_class=HTMLResponse
)
def exercicio_aula_02():
    return """
    <html>
        <head>
            <title>Nosso Hello world!</title>
        </head>
        <body>
            <h1>Hello world!</h1>
        </body>
    </html>"""
