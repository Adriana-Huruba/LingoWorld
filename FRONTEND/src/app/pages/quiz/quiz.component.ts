import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

interface QuizExercise {
  exercise_id: number;
  level: string;
  type: string;
  content: {
    exercise_title: string;
    questions: Array<{question: string; answer: string; options?: string[];}>;
  };
}

interface QuizResponse {
  exercise_id: number;
  level: string;
  is_correct: boolean;
}

@Component({
  selector: 'app-quiz',
  imports: [CommonModule, FormsModule],
  templateUrl: './quiz.component.html',
  styleUrl: './quiz.component.scss'
})

export class QuizComponent {
  private authService= inject(AuthService);
  private http = inject(HttpClient);
  private router = inject(Router);
  private apiUrl = 'http://localhost:8000/api';
  private User=inject(AuthService);

  currentStep: 'agreement' | 'level' | 'loading' | 'quiz' | 'exercises' | 'result'= 'agreement';
  
  selectedLanguage: any = null;
  selectedLevel: any = null;
  exercises: QuizExercise[]  = [];
  currentIndex = 0;
  selectedOption: string = '';
  textAnswer: string  = '';
  responses: QuizResponse[] = [];

  result: {
    estimated_level: string;
    starting_elo: number;
    score_percent: number;
    correct: number;
    total: number;
  } | null = null;
 
  error: string | null = null;

  languages = [
    { id: 'english', name: 'English', flag: '🇬🇧' },
    { id: 'romanian', name: 'Română', flag: '🇷🇴' },
    { id: 'french', name: 'Francais', flag: '🇫🇷' },
    { id: 'spanish', name: 'Español', flag: '🇪🇸' }
  ];

  levels = [
    { id: 'A1', description: 'Beginner' },
    { id: 'A2', description: 'Elementary' },
    { id: 'B1', description: 'Intermediate' },
    { id: 'B2', description: 'Upper Intermediate' },
    { id: 'C1', description: 'Advanced' },
    { id: 'C2', description: 'Proficient' }
  ];

  startQuiz() {
    this.currentStep = 'level';
  }

  get currentExercise(): QuizExercise | null {
    return this.exercises[this.currentIndex] ?? null;
  }
 
  get currentQuestion() {
    return this.currentExercise?.content.questions[0] ?? null;
  }
 
  get isLastExercise(): boolean {
    return this.currentIndex === this.exercises.length - 1;
  }
 
  get progressPercent(): number {
    if (!this.exercises.length) 
      return 0;
    return Math.round((this.currentIndex / this.exercises.length) * 100);
  }
 
  get canSubmit(): boolean {
    if (!this.currentExercise) 
      return false;
    if (this.currentExercise.type === 'multiple-choice') 
      return !!this.selectedOption;
    return this.textAnswer.trim().length > 0;
  }

  loadExercises(): void {
    this.error = null;
    const langCode = this.authService.normalizeLanguage(this.selectedLanguage.id);
 
    this.http.get<any>(`${this.apiUrl}/initial-quiz/${langCode}`
    ).subscribe({
      next: (res) => {
        this.exercises  = res.exercises;
        this.currentIndex = 0;
        this.responses = [];
        this.currentStep = 'quiz';
      },
      error: (err) => {
        this.error = err.error?.detail ?? 'Could not load exercises.';
        this.currentStep = 'level'; 
      },
    });
  }

  selectLevel(level: any) {
    if (!this.selectedLanguage) {
      alert('Please select a language first!');
      return;
    }
    this.selectedLevel = level;
    this.currentStep = 'loading';
    this.loadExercises();
  }

  selectOption(option: string): void {
    this.selectedOption = option;
  }
 
  confirmAnswer(): void {
    const question = this.currentQuestion;
    const exercise = this.currentExercise;
    if (!question || !exercise) 
      return;
 
    const userAnswer = this.currentExercise!.type === 'multiple-choice'? this.selectedOption: this.textAnswer.trim();
    const isCorrect = userAnswer.toLowerCase() === question.answer.toLowerCase();

    this.responses.push({
      exercise_id: exercise.exercise_id,
      level: exercise.level,
      is_correct: isCorrect,
    });
 
    if (this.isLastExercise) 
      this.submitResults();
    else {
      this.currentIndex++;
      this.selectedOption = '';
      this.textAnswer = '';
    }
  }

  submitResults(): void {
    const userId = this.authService.currentUserId;
    this.currentStep = 'loading';
 
    const langCode = this.authService.normalizeLanguage(this.selectedLanguage.id);

    this.http.post<any>(`${this.apiUrl}/initial-quiz/submit`,
      {
        user_id: userId,
        language: langCode,
        responses: this.responses,
      }
    ).subscribe({
      next: (res) => {
        this.result  = res;
        this.currentStep = 'result';
      },
      error: (err) => {
        this.error = err.error?.detail ?? 'Could not save results.';
        this.currentStep = 'quiz';
      },
    });
  }

  goToDashboard(): void {
    this.router.navigate(['/homepage']);
  }

  getOptionLabel(index: number): string {
    return ['A', 'B', 'C', 'D'][index] ?? `${index + 1}`;
  }
}
