from app.database.sqlite import database
from app.database.sqlite.dto.roleDto import RoleDto


class RoleDao:
    def add(code: str, name: str, description: str):
        """
        add new role
        Parameters
        ----------
        code : str
            memorizable code for quickly referencing a role. Example: Administrator with code: admin or administrator
        name : str
            readable and self-explainable role name (unique column)
        description : str
            short description of the role
        """
        role = RoleDto(code=code, name=name, description=description)
        database.session.add(role)
        database.session.commit()
        return role

    def get_role_by_id(id: int):
        """
        get role by role id (primary key)
        Parameters
        ----------
        id : int
        """
        return RoleDto.query.get(id)

    def get_role_by_code(code: str):
        """
        get role by memorizable code (unique column)
        Parameters
        ----------
        code : str
        """
        return RoleDto.query.filter(RoleDto.code == code).one_or_none()
