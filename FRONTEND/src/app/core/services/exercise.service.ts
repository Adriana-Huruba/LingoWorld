import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ExerciseService {
  private apiUrl = 'http://localhost:8000/generate-exercise';
  constructor(private http: HttpClient) {}

  generateExercise(data: any) {
    return this.http.post<any>(this.apiUrl, {
      topic: data.topic,
      type: data.type,
      level: data.level
    });
  }
}