from dao.classroom_dao import ClassroomDAO

class ClassroomService:
    @staticmethod
    def create_new_class(name, teacher_id):
        if not name or len(name) < 3:
            return None
        return ClassroomDAO.create_classroom_db(name, teacher_id)
    
    @staticmethod
    def get_teacher_classrooms(teacher_id):
        return ClassroomDAO.get_classrooms_by_teacher(teacher_id)

    @staticmethod
    def get_classroom(classroom_id):
        return ClassroomDAO.get_classroom_by_id(classroom_id)

    @staticmethod
    def get_classroom_students(classroom_id):
        return ClassroomDAO.get_students_by_classroom(classroom_id)