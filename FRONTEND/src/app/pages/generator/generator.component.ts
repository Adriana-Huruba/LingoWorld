import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ExerciseService } from '../../core/services/exercise.service';
import { AuthService } from '../../core/services/auth.service';
import { UniversalPlayerComponent, PlayerQuestion } from '../universal-player/universal-player.component';
import { QuizMode } from '../../core/enums/quiz-mode.enum';

@Component({
  selector: 'app-generator',
  imports: [CommonModule, FormsModule, UniversalPlayerComponent],
  templateUrl: './generator.component.html',
  styleUrl: './generator.component.scss'
})
export class GeneratorComponent implements OnInit {
  authService = inject(AuthService);
  private exerciseService = inject(ExerciseService);

  topics: string[] = [];
  selectedTopic: string = '';
  selectedSkillType: string = '';
  selectedCount: number = 5;

  readonly skillTypes = [
    { value: '', label: 'Any' },
    { value: 'grammar', label: 'Grammar' },
    { value: 'vocabulary', label: 'Vocabulary' },
    { value: 'reading', label: 'Reading' },
    { value: 'writing', label: 'Writing' },
  ];

  readonly countOptions = [3, 5, 10];

  isLoading = false;
  errorMessage: string | null = null;

  showPlayer = false;
  generatedQuestions: PlayerQuestion[] = [];
  QuizMode = QuizMode;

  ngOnInit() {
    const language = this.authService.targetLanguageFull;
    const level = this.authService.userLevel;
    this.exerciseService.getTopics(language, level).subscribe({
      next: (data) => {
        const seen = new Set<string>();
        this.topics = data
          .map(t => t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).trim())
          .filter(t => { const k = t.toLowerCase(); if (seen.has(k)) return false; seen.add(k); return true; });
      }
    });
  }

  startSession() {
    if (this.isLoading) return;
    this.isLoading = true;
    this.errorMessage = null;

    const userId = this.authService.currentUserId();
    const language = this.authService.targetLanguageFull;
    const topic = this.selectedTopic || undefined;
    const skillType = this.selectedSkillType || undefined;

    const requests = Array(this.selectedCount).fill(null).map(() =>
      this.exerciseService.getNextExercise({
        user_id: userId,
        target_language: language,
        topic,
        skill_type: skillType,
        allow_generation: true,
      }).pipe(catchError(() => of(null)))
    );

    forkJoin(requests).subscribe(results => {
      const questions = results.filter(Boolean) as unknown as PlayerQuestion[];
      if (questions.length === 0) {
        this.errorMessage = 'No exercises could be generated. Try again later.';
        this.isLoading = false;
        return;
      }
      this.generatedQuestions = questions;
      this.showPlayer = true;
      this.isLoading = false;
    });
  }

  onPlayerClosed() {
    this.showPlayer = false;
    this.generatedQuestions = [];
  }

  onPlayerCompleted(result: any) {
    this.showPlayer = false;
    this.generatedQuestions = [];
  }
}