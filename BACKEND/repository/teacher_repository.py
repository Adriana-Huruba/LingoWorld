from dao.teacher_dao import TeacherDAO

class TeacherRepository:
    @staticmethod
    def save_manual_metadata(teacher_id, filename, title, language, level, total_pages, total_chunks, chapters, conn, file_hash=None) -> int:
        try:
            manual_id = TeacherDAO.insert_manual(teacher_id, filename, title, language, level, total_pages, total_chunks, chapters, conn, file_hash=file_hash)
            conn.commit()
            return manual_id
        except Exception as e:
            conn.rollback()
            raise e
        
    @staticmethod
    def set_manual_as_active(manual_id, conn):
        try:
            TeacherDAO.mark_manual_processed(manual_id, conn)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        
    @staticmethod
    def get_manual_by_id(manual_id, teacher_id, conn) -> dict:
            return TeacherDAO.get_manual(manual_id, teacher_id, conn)
    
    @staticmethod
    def list_manuals(teacher_id, conn):
        return TeacherDAO.list_manuals_for_teacher(teacher_id, conn)

    @staticmethod
    def find_manual_by_filename(teacher_id, filename, conn):
        return TeacherDAO.find_manual_by_filename(teacher_id, filename, conn)

    @staticmethod
    def find_manual_by_hash(teacher_id, file_hash, conn):
        return TeacherDAO.find_manual_by_hash(teacher_id, file_hash, conn)

    @staticmethod
    def delete_manual(manual_id, teacher_id, conn) -> bool:
        try:
            deleted = TeacherDAO.delete_manual(manual_id, teacher_id, conn)
            conn.commit()
            return deleted
        except Exception as e:
            conn.rollback()
            raise e
    
    @staticmethod
    def list_worksheets(teacher_id, conn) -> list[dict]:
        return TeacherDAO.list_worksheets_for_teacher(teacher_id, conn)

    @staticmethod
    def get_worksheet_progress(worksheet_id, teacher_id, conn) -> dict | None:
        return TeacherDAO.get_worksheet_progress(worksheet_id, teacher_id, conn)
        
    @staticmethod
    def publish_complete_worksheet(payload, conn) -> dict:
        try:
            manual = TeacherDAO.get_manual(payload.manual_id, payload.teacher_id, conn)
            if not manual:
                raise ValueError("Textbook not found or you do not have acces to it.")
            
            items_dict = [item.model_dump() for item in payload.items]
            
            result = TeacherDAO.publish_worksheet_from_items(
                teacher_id=payload.teacher_id,
                manual_id=payload.manual_id,
                classroom_id=payload.classroom_id,
                title=payload.title,
                items=items_dict,
                language=manual["language"],
                level=manual["level"],
                source_manual=manual["filename"],
                due_date=payload.due_date,
                config=payload.config,
                conn=conn
            )

            conn.commit()
            return result
            
        except Exception as e:
            conn.rollback()
            raise e
    