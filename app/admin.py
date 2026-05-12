from sqladmin import Admin, ModelView

from app.core.database import db
from app.models.department import Department


class DepartmentAdmin(ModelView, model=Department):
    column_list = [Department.id, Department.name, Department.parent_id, Department.created_at]
    column_searchable_list = [Department.name]
    column_sortable_list = [Department.id, Department.name, Department.created_at]


def setup_admin(app) -> Admin:
    admin = Admin(app, db.engine, base_url="/admin")
    admin.add_view(DepartmentAdmin)
    return admin
