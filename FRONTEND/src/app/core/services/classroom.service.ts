import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})

export class ClassroomService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = 'http://localhost:8000/api/classrooms';

  createClassroom(className: string): Observable<any> {
    const teacherId = this.authService.currentUserId(); 

    if (!teacherId) {
      console.error("Did not find the teacher's ID!");
    }

    const body = { 
      name: className, 
      teacher_id: teacherId 
    };

    return this.http.post(`${this.apiUrl}/create`, body);
  }

  getClassroomsOfTeacher(): Observable<any> {
    const teacherId = this.authService.currentUserId();
    return this.http.get(`${this.apiUrl}/all/${teacherId}`);
  }

  getClassroomById(classroomId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/${classroomId}`);
  }

  getClassroomStudents(classroomId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/${classroomId}/students`);
  }
}