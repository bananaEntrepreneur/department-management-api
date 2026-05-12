from sqladmin import Admin, ModelView

from app.core.database import db
from app.models.department import Department
from app.models.employee import Employee


class DepartmentAdmin(ModelView, model=Department):
    column_list = [Department.id, Department.name, Department.parent_id, Department.created_at]
    column_searchable_list = [Department.name]
    column_sortable_list = [Department.id, Department.name, Department.created_at]


class EmployeeAdmin(ModelView, model=Employee):
    column_list = [
        Employee.id,
        Employee.department_id,
        Employee.full_name,
        Employee.position,
        Employee.hired_at,
        Employee.created_at,
    ]
    column_searchable_list = [Employee.full_name, Employee.position]
    column_sortable_list = [Employee.id, Employee.full_name, Employee.position, Employee.created_at]


def setup_admin(app) -> Admin:
    admin = Admin(app, db.engine, base_url="/admin")
    admin.add_view(DepartmentAdmin)
    admin.add_view(EmployeeAdmin)
    return admin
