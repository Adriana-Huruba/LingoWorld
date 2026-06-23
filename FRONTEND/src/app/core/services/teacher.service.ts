import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})

export class TeacherService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  getTeacherManuals(teacherId: number) {
    const params = new HttpParams().set('teacher_id', teacherId.toString());
    return this.http.get<any[]>('http://localhost:8000/api/manuals', { params })
  }

  uploadManual(file: File, teacherId: number, title: string, language: string, level: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('teacher_id', teacherId.toString());
    formData.append('title', title);
    formData.append('language', language);
    formData.append('level', level);

    return this.http.post(`${this.apiUrl}/manuals/upload`, formData);
  }

  deleteManual(manualId: number, teacherId: number): Observable<any> {
    const params = new HttpParams().set('teacher_id', teacherId.toString());
    return this.http.delete(`${this.apiUrl}/manuals/${manualId}`, { params });
  }

  previewWorksheet(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/worksheets/preview`, payload);
  }

    regenerateItem(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/worksheets/regenerate-item`, payload);
  }

  publishWorksheet(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/worksheets/publish`, payload);
  }

  getWorksheetsByClassroom(classroomId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/worksheets/classroom/${classroomId}`);
  }
}
