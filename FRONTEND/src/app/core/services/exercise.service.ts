import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { AuthService } from './auth.service';
import { tap } from 'rxjs';

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
  
  getNextExercise(payload: { user_id: number; target_language: string; skill_type?: string; topic?: string; allow_generation?: boolean }) {
    return this.http.post<ExerciseResponse>(`${this.apiUrl}/next-exercise`, payload);
  }

  submitAnswer(payload: 
    {user_id: number; 
      exercise_id: number; 
      is_correct: boolean; 
      response_time_seconds: number; 
      exercise_type: string;
      used_hint: boolean;
      assignment_id?: number;}) {
    return this.http.post<any>(`${this.apiUrl}/submit-answer`, payload).pipe(
      tap((response) => {
        if (response && response.new_xp !== undefined && response.new_elo !== undefined) {
          this.authService.userXp.set(response.new_xp);
          this.authService.userElo.set(response.new_elo);
        } 
        else {
          const lang = this.authService.targetLanguageFull;
          this.getUserProgress(payload.user_id, lang).subscribe(data => {
            this.authService.userXp.set(data.xp);
            this.authService.userElo.set(data.current_elo);
          });
        }
      })
    );
  }

  getHint(payload: { exercise_id: number; exercise_type: string; language: string; native_language?: string; level: string }) {
    return this.http.post<{ hint: string }>(`${this.apiUrl}/hint`, payload);
  }

  getTopics(language?: string, level?: string) {
    const p: Record<string, string> = {};
    if (language) 
      p['language'] = language;
    if (level)    
      p['level'] = level;
    return this.http.get<string[]>(`${this.apiUrl}/alltopics`, { params: p });
  }

  getUserProgress(userId: number, language: string) {
    return this.http.get<any>(`${this.apiUrl}/progress/${userId}`, { params: { language } });
  }

  getInitialQuiz(language: string) {
    return this.http.get<any>(`${this.apiUrl}/initial-quiz/${language}`);
  }

  submitInitialQuiz(payload: { user_id: number; language: string; responses: any[] }) {
    return this.http.post<any>(`${this.apiUrl}/initial-quiz/submit`, payload);
  }

  hasCompletedQuiz(userId: number) {
    return this.http.get<any>(`${this.apiUrl}/initial-quiz/completed/${userId}`);
  }
}
