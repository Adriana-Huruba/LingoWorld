import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { TeacherClassroom, StudentClassroom, ClassroomStudent, StudentProgress, Worksheet} from '../interfaces/classroom.interface';

@Injectable({
  providedIn: 'root'
})

export class ClassroomService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = 'http://localhost:8000/api/classrooms';

  createClassroom(className: string): Observable<{ invite_code: string }> {
    const teacherId = this.authService.currentUserId();

    if (!teacherId) {
      console.error("Did not find the teacher's ID!");
    }

    return this.http.post<{ invite_code: string }>(`${this.apiUrl}/create`, {
      name: className,
      teacher_id: teacherId,
    });
  }

  enrollStudent(studentId: number, inviteCode: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/enroll`, {
      student_id: studentId,
      invite_code: inviteCode,
    });
  }

  getClassroomsOfTeacher(): Observable<{ classrooms: TeacherClassroom[] }> {
    const teacherId = this.authService.currentUserId();
    return this.http.get<{ classrooms: TeacherClassroom[] }>(`${this.apiUrl}/all/${teacherId}`);
  }

  getClassroomById(classroomId: number): Observable<{ id: number; name: string; invite_code: string }> {
    return this.http.get<{ id: number; name: string; invite_code: string }>(`${this.apiUrl}/${classroomId}`);
  }

  getClassroomStudents(classroomId: number): Observable<{ students: ClassroomStudent[] }> {
    return this.http.get<{ students: ClassroomStudent[] }>(`${this.apiUrl}/${classroomId}/students`);
  }

  getStudentClassrooms(studentId: number): Observable<{ classrooms: StudentClassroom[] }> {
    return this.http.get<{ classrooms: StudentClassroom[] }>(`${this.apiUrl}/student-classes/${studentId}`);
  }

  getClassroomAssignments(classroomId: number): Observable<{ assignments: Worksheet[] }> {
    return this.http.get<{ assignments: Worksheet[] }>(`${this.apiUrl}/${classroomId}/assignments`);
  }

  getAssignmentById(assignmentId: number): Observable<Worksheet> {
    return this.http.get<Worksheet>(`${this.apiUrl}/assignments/${assignmentId}`);
  }

  getStudentProgress(classroomId: number): Observable<{ students: StudentProgress[] }> {
    return this.http.get<{ students: StudentProgress[] }>(`${this.apiUrl}/${classroomId}/student-progress`);
  }

  completeWorksheet(studentId: number, worksheetId: number, score: number, total: number): Observable<{ success: boolean }> {
    return this.http.post<{ success: boolean }>(`${this.apiUrl}/complete-worksheet`, {
      student_id: studentId,
      worksheet_id: worksheetId,
      score,
      total,
    });
  }
}
