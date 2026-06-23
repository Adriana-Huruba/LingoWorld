import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AuthService } from '../../core/services/auth.service';
import { ExerciseService } from '../../core/services/exercise.service';
import { TeacherDashboardComponent } from '../teacher/teacher-dashboard/teacher-dashboard.component';
import { StudentDashboardComponent } from '../student/student-dashboard/student-dashboard.component';
import { UniversalPlayerComponent, PlayerQuestion } from '../universal-player/universal-player.component';
import { QuizMode } from '../../core/enums/quiz-mode.enum';
import { Router } from '@angular/router';

@Component({
  selector: 'app-homepage',
  standalone: true,
  imports: [CommonModule, TeacherDashboardComponent, StudentDashboardComponent, UniversalPlayerComponent],
  templateUrl: './homepage.component.html',
  styleUrl: './homepage.component.scss'
})

export class HomepageComponent implements OnInit {
  public authService = inject(AuthService);
  private exerciseService = inject(ExerciseService);
  private router = inject(Router);

  topics: string[] = [];

  showPlayer = false;
  playerQuestions: PlayerQuestion[] = [];
  playerTitle = '';
  isLoadingExercises = false;
  QuizMode = QuizMode;

  private readonly SESSION_SIZE = 5;

  ngOnInit() {
    if (this.authService.userRole() === 'adult_learner') {
      this.loadTopics();
    }
  }

  loadTopics() {
    const language = this.authService.targetLanguageFull;
    const level    = this.authService.userLevel;
    this.exerciseService.getTopics(language, level).subscribe({
      next: (data) => {
        const seen = new Set<string>();
        this.topics = data
          .map(t => t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).trim())
          .filter(t => { const k = t.toLowerCase(); if (seen.has(k)) return false; seen.add(k); return true; });
      },
      error: (err) => { console.error('Error loading topics:', err); }
    });
  }

  startDailyReview() {
    this.launchSession('Daily Review', undefined);
  }

  startTopicSession(topic: string) {
    this.launchSession(topic, topic);
  }

  private launchSession(title: string, topic?: string) {
    if (this.isLoadingExercises) return;
    this.isLoadingExercises = true;

    const userId = this.authService.userId;
    const language = this.authService.targetLanguageFull;

    const dbRequests = Array(2).fill(null).map(() =>
      this.exerciseService.getNextExercise({ user_id: userId, target_language: language, topic, allow_generation: false })
        .pipe(catchError(() => of(null)))
    );

    forkJoin(dbRequests).subscribe({
      next: (results) => {
        const validDbEx = results.filter(Boolean) as unknown as PlayerQuestion[];
        
        if (validDbEx.length > 0) {

          this.playerQuestions = validDbEx;
          this.playerTitle = title;
          this.showPlayer = true;
          this.isLoadingExercises = false;

  
          this.fetchBackgroundExercises(userId, language, topic, 3, false);
        } else {
      
          console.log('[Homepage] Empty bd. waiting for ai generation...');
          this.fetchBackgroundExercises(userId, language, topic, 5, true);
        }
      },
      error: () => { this.isLoadingExercises = false; }
    });
  }

  private fetchBackgroundExercises(userId: number, language: string, topic: string | undefined, count: number, isBlocking: boolean) {
    const bgRequests = Array(count).fill(null).map(() =>
      this.exerciseService.getNextExercise({ user_id: userId, target_language: language, topic, allow_generation: true })
        .pipe(catchError(() => of(null)))
    );

    forkJoin(bgRequests).subscribe(results => {
      const newQuestions = results.filter(Boolean) as unknown as PlayerQuestion[];
      
      if (newQuestions.length > 0) {
        this.playerQuestions = [...this.playerQuestions, ...newQuestions];
      }

      if (isBlocking) {
        if (this.playerQuestions.length > 0) {
          this.showPlayer = true;
        } else {
          console.warn('[Homepage] AI could not generate exercises');
        }
        this.isLoadingExercises = false;
      }
    });
  }

  onPlayerClosed() {
    this.showPlayer = false;
    this.playerQuestions = [];
  }

  onPlayerCompleted(result: { score: number; total: number }) {
    this.showPlayer = false;
    this.playerQuestions = [];
    console.log('[Homepage] Session done: ' + result.score + '/' + result.total);
  }

  redirectToGenerator() {
    this.router.navigate(['/generator']);
  }
}
