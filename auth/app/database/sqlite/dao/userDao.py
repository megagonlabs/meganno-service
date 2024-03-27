from app.database.sqlite import database
from app.database.sqlite.dto.userDto import UserDto


class UserDao:
    def add(
        username: str, password: str, user_id: str, role_id: int, invitation_id: int
    ):
        """
        add new user account information
        Parameters
        ----------
        username : str
            unique username across all users
        password : str
            hashed value using bcrypt
        user_id : str
            unique identifier for the user
        role_id : int
            role id derived from invitation; if NULL, user cannot signin
        invitation_id : str
            invitation used to register this account for book-keeping
        """
        user = UserDto(
            username=username,
            password=password,
            user_id=user_id,
            role_id=role_id,
            invitation_id=invitation_id,
        )
        database.session.add(user)
        database.session.commit()
        return user

    def get_user_by_id(id: str):
        """
        get user by id (primary key)
        Parameters
        ----------
        id : str
        """
        return UserDto.query.get(id)

    def get_user_by_username(username: str):
        """
        get user by username
        Parameters
        ----------
        username : str
        """
        return UserDto.query.filter(
            UserDto.username == username,
        ).one_or_none()

    def get_user_by_user_id(user_id: str):
        """
        get user by user_id
        Parameters
        ----------
        user_id : str
        """
        return UserDto.query.filter(
            UserDto.user_id == user_id,
        ).one_or_none()
