import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { AuthService } from './auth.service';

export interface ExerciseResponse {
  exercise_id: number;
  language: string;
  level: string;
  type: string;
  skill_type: string;
  topic: string;
  content: {
    exercise_title: string;
    questions: Array<{question: string; answer: string; options: string[];}>;
  };
  correct_answer: string;
  elo_difficulty: number;
  source_manual: string;
  points: number;
  reason: string;
}

@Injectable({ providedIn: 'root' })

export class ExerciseService {
  private apiUrl = 'http://localhost:8000/api';
  authService = inject(AuthService);
  constructor(private http: HttpClient) {}

  generateExercise(data: any) {
    return this.http.post<any>(`${this.apiUrl}/generate-exercise`, data);
  }
  
  getNextExercise(payload: { user_id: number; target_language: string; skill_type?: string; topic?: string }) {
    return this.http.post<ExerciseResponse>(`${this.apiUrl}/next-exercise`, payload);
  }

  submitAnswer(payload: {user_id: number; exercise_id: number; is_correct: boolean; response_time_seconds: number; exercise_type: string; used_hint: boolean;}) {
    return this.http.post<any>(`${this.apiUrl}/submit-answer`, payload);
  }

  getTopics() {
    return this.http.get<string[]>(`${this.apiUrl}/alltopics`);
  }
}