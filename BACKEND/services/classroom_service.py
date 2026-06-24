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
    
    @staticmethod
    def enroll_student(student_id, invite_code):
        if not invite_code:
            return False, "Invite code can't be empty!"
        return ClassroomDAO.enroll_student(student_id, invite_code)
    
    @staticmethod
    def get_student_classrooms(student_id):
        if not student_id:
            return []
        return ClassroomDAO.get_classrooms_by_student(student_id)
    
    @staticmethod
    def get_classroom_assignments(classroom_id, student_id=None):
        return ClassroomDAO.get_classroom_assignments(classroom_id, student_id=student_id)

    @staticmethod
    def get_pending_assignments_for_student(student_id):
        return ClassroomDAO.get_pending_assignments_for_student(student_id)

    @staticmethod
    def get_student_progress(classroom_id):
        return ClassroomDAO.get_student_progress_for_classroom(classroom_id)

    @staticmethod
    def complete_worksheet(student_id, worksheet_id, score, total):
        return ClassroomDAO.save_worksheet_completion(student_id, worksheet_id, score, total)