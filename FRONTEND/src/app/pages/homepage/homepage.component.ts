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

  topics: { id: string, name: string }[] = [];

  showPlayer = false;
  playerQuestions: PlayerQuestion[] = [];
  playerTitle = '';
  isLoadingExercises = false;
  noDueExercises = false;
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
          .map(t => ({
            id: t,
            name: t.replace(/_/g, ' ').replace(/\s+/g, ' ').trim().replace(/\b\w/g, c => c.toUpperCase())
          }))
          .filter(t => {
            const key = t.name.toLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
          });
      },
      error: (err) => { console.error('Error loading topics:', err); }
    });
  }

  startDailyReview() {
    if (this.isLoadingExercises) 
      return;
    this.isLoadingExercises = true;
    this.noDueExercises = false;

    const userId = this.authService.userId;
    const language = this.authService.targetLanguageFull;

    this.exerciseService.getDueExercises(userId, language).subscribe({
      next: (data) => {
        if (!data.exercises.length) {
          this.noDueExercises = true;
          setTimeout(() => this.noDueExercises = false, 4000);
          this.isLoadingExercises = false;
          return;
        }
        this.playerQuestions = data.exercises as unknown as PlayerQuestion[];
        this.playerTitle = 'Daily Review';
        this.showPlayer = true;
        this.isLoadingExercises = false;
      },
      error: () => { this.isLoadingExercises = false; }
    });
  }

  startTopicSession(topic: { id: string, name: string }) {
    this.launchSession(topic.name, topic.id);
  }

  private launchSession(title: string, topic?: string) {
    if (this.isLoadingExercises) return;
    this.isLoadingExercises = true;

    const userId = this.authService.userId;
    const language = this.authService.targetLanguageFull;

    const isDailyReview = topic === undefined;
    const dbRequests = Array(5).fill(null).map(() =>
      this.exerciseService.getNextExercise({ user_id: userId, target_language: language, topic, allow_generation: false, spaced_repetition_only: isDailyReview })
        .pipe(catchError(() => of(null)))
    );

    forkJoin(dbRequests).subscribe({
      next: (results) => {
        const validDbEx = results.filter(Boolean) as unknown as PlayerQuestion[];
        const uniqueDbEx = Array.from(new Map(validDbEx.map(item => [item.exercise_id, item])).values());

        if (uniqueDbEx.length > 0) {
          this.playerQuestions = uniqueDbEx;
          this.playerTitle = title;
          this.showPlayer = true;
          this.isLoadingExercises = false;

          const remaining = 5 - uniqueDbEx.length;
          if (remaining > 0 && !isDailyReview) {
            console.log(`[Homepage] Found ${uniqueDbEx.length} in DB. Generating ${remaining} in background...`);
            this.fetchBackgroundExercises(userId, language, topic, remaining, false);
          }
        } else if (!isDailyReview) {
          console.log('[Homepage] No ready exercises found. Waiting for AI generation...');
          this.fetchBackgroundExercises(userId, language, topic, 5, true);
        } else {
          console.log('[Homepage] No due exercises for daily review.');
          this.noDueExercises = true;
          this.isLoadingExercises = false;
          setTimeout(() => this.noDueExercises = false, 4000);
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
