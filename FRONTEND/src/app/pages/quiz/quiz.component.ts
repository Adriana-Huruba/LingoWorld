import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
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

export class QuizComponent implements OnInit{
  private authService = inject(AuthService);
  private exerciseService = inject(ExerciseService);
  private router = inject(Router);

  currentStep: 'agreement' | 'level' | 'loading' | 'quiz' | 'exercises' | 'result'= 'loading';
  isQuizPaused: boolean = false;
  
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
  QuizMode = QuizMode;

  ngOnInit(): void {
    const userId = this.authService.currentUserId(); 
    
    this.exerciseService.hasCompletedQuiz(userId).subscribe({
      next: (res) => {
        if (res.completed) { 
          this.goToDashboard();
        } else {
          this.currentStep = 'agreement';
        }
      },
      error: (err) => {
        console.error('Eroror at checking if the quiz was completed:', err);
        this.currentStep = 'agreement'; 
      }
    });
  }

  startQuiz() {
    this.currentStep = 'loading';
    this.loadExercises();
  }

  loadExercises(): void {
    this.error = null;
    const targetLang = this.authService.targetLanguageFull.toLowerCase(); 

    this.exerciseService.getInitialQuiz(targetLang).subscribe({
      next: (res) => {
        this.exercises = res.exercises;
        this.responses = [];
        this.currentStep = 'quiz';
      },
      error: (err) => {
        this.error = err.error?.detail ?? 'Could not load exercises.';
        this.currentStep = 'agreement';
      },
    });
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
    
    const targetLang = this.authService.targetLanguageFull.toLowerCase();

    this.exerciseService.submitInitialQuiz({
      user_id: userId,
      language: targetLang,
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

  onQuizClosed(): void {
    this.isQuizPaused = true;
  }

  resumeQuiz(): void {
    this.isQuizPaused = false;
  }

  goToDashboard(): void {
    this.router.navigate(['/homepage']);
  }
}
