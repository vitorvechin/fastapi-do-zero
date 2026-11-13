from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fast_zero.database import get_session
from fast_zero.models import User as UserModel
from fast_zero.schemas import (
    Message,
    UserList,
    UserPublic,
)
from fast_zero.schemas import (
    User as UserSchema,
)
from fast_zero.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)

app = FastAPI()


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Hello world!'}


@app.post('/users', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session = Depends(get_session)):

    db_user = session.scalar(
        select(UserModel).where(
            (UserModel.username == user.username)
            | (UserModel.email == user.email)
        )
    )

    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                HTTPStatus.CONFLICT, detail='Username already exists'
            )

        else:
            raise HTTPException(
                HTTPStatus.CONFLICT, detail='Email already exists'
            )

    db_user = UserModel(
        **user.model_dump(exclude={'password'}),
        password=get_password_hash(user.password),
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@app.get('/users', status_code=HTTPStatus.OK, response_model=UserList)
def read_users(
    limit: int = 10, offset: int = 0, session: Session = Depends(get_session)
):

    users = session.scalars(select(UserModel).limit(limit).offset(offset))
    return {'users': users}


@app.get('/users/{user_id}', response_model=UserPublic)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(UserModel).where(UserModel.id == user_id))

    if not user_db:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='User not found')

    return user_db


@app.put('/users/{user_id}', response_model=UserPublic)
def update_user(
    user_id: int, user: UserSchema, session: Session = Depends(get_session)
):
    user_db = session.scalar(select(UserModel).where(UserModel.id == user_id))

    if not user_db:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='User not found')

    try:
        user_db.username = user.username
        user_db.email = user.email
        user_db.password = get_password_hash(user.password)

        # add is not needed here since the user_db is already in the session
        session.commit()
        session.refresh(user_db)

        return user_db

    except IntegrityError:
        raise HTTPException(
            HTTPStatus.CONFLICT, detail='Username or email already exists'
        )


@app.delete('/users/{user_id}', response_model=Message)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(UserModel).where(UserModel.id == user_id))

    if not user_db:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='User not found')

    session.delete(user_db)
    session.commit()

    return {'message': 'User deleted'}


@app.post('/token')
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):

    user = session.scalar(
        select(UserModel).where(UserModel.email == form_data.username)
    )

    if not user:
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, detail='Incorret email or password'
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, detail='Incorret email or password'
        )

    payload = {'sub': user.email}
    access_token = create_access_token(payload)

    return {'access_token': access_token, 'token_type': 'bearer'}
