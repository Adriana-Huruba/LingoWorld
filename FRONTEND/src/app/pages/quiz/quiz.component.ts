import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ExerciseService } from '../../core/services/exercise.service';
import { UniversalPlayerComponent } from '../universal-player/universal-player.component';
import { QuizMode } from '../../core/enums/quiz-mode.enum';
import { NzIconModule } from 'ng-zorro-antd/icon';

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
  imports: [CommonModule, FormsModule, UniversalPlayerComponent, NzIconModule],
  templateUrl: './quiz.component.html',
  styleUrl: './quiz.component.scss'
})

export class QuizComponent {
  private authService = inject(AuthService);
  private exerciseService = inject(ExerciseService);
  private router = inject(Router);

  currentStep: 'agreement' | 'level' | 'loading' | 'quiz' | 'exercises' | 'result'= 'agreement';
  
  selectedLanguage: any = null;
  selectedLevel: any = null;
  exercises: QuizExercise[]  = [];
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

  QuizMode = QuizMode;

  startQuiz() {
    this.currentStep = 'level';
  }

  loadExercises(): void {
    this.error = null;
    this.exerciseService.getInitialQuiz(this.selectedLanguage.id).subscribe({
      next: (res) => {
        this.exercises = res.exercises;
        this.responses = [];
        this.currentStep = 'quiz';
      },
      error: (err) => {
        this.error = err.error?.detail ?? 'Could not load exercises.';
        this.currentStep = 'level';
      },
    });
  }

  selectLevel(level: any): void {
    if (!this.selectedLanguage) {
      alert('Please select a language first!');
      return;
    }
    this.selectedLevel = level;
    this.currentStep = 'loading';
    this.loadExercises();
  }


  onQuizCompleted(event: {
    score: number;
    total: number;
    responses?: Array<{ exercise_id: number; level: string; is_correct: boolean }>;
  }): void {
    if (event.responses?.length) {
      this.responses = event.responses;
    }
    this.submitResults();
  }

  submitResults(): void {
    const userId = this.authService.currentUserId();
    this.currentStep = 'loading';
    const langCode = this.selectedLanguage.id; 

    this.exerciseService.submitInitialQuiz({
      user_id: userId,
      language: langCode,
      responses: this.responses,
    }).subscribe({
      next: (res) => {
        this.result = res;
        this.currentStep = 'result';
     
        if (res.estimated_level) 
          this.authService.updateLevel(res.estimated_level);
        if (res.starting_elo != null) 
          this.authService.updateElo(res.starting_elo);
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
}
