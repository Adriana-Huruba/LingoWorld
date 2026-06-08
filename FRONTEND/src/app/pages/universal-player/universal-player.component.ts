import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { QuizMode } from '../../core/enums/quiz-mode.enum';

export interface PlayerQuestion {
  question: string;
  options: string[];
  answer: string;
}

@Component({
  selector: 'app-universal-player',
  standalone: true,
  imports: [CommonModule, NzIconModule],
  templateUrl: './universal-player.component.html',
  styleUrl: './universal-player.component.scss'
})

export class UniversalPlayerComponent implements OnInit {
  @Input() mode!: QuizMode;
  @Input() title: string = '';
  @Input() topicContext?: string;
  @Input() assignmentId?: number;
  @Input() preloadedExercises?: any[];

  @Output() closed = new EventEmitter<void>();
  @Output() completed = new EventEmitter<{ score: number; total: number }>();

  public QuizMode = QuizMode;

  questions: PlayerQuestion[] = [];
  currentQuestionIndex = 0;
  selectedOption = '';
  answered = false;
  isCorrect = false;
  score = 0;
  sessionFinished = false;

  ngOnInit(): void {
    if (this.preloadedExercises?.length) {
      this.questions = this.normalizeQuestions(this.preloadedExercises);
    }
  }

  private normalizeQuestions(raw: any[]): PlayerQuestion[] {
    return raw.map(item => {
      if (item.question !== undefined && item.options !== undefined) {
        return { question: item.question, options: item.options ?? [], answer: item.answer };
      }

      if (item.content?.questions?.length) {
        const q = item.content.questions[0];
        return { question: q.question, options: q.options ?? [], answer: q.answer };
      }
      return item as PlayerQuestion;
    });
  }

  get currentQuestion(): PlayerQuestion | null {
    return this.questions[this.currentQuestionIndex] ?? null;
  }

  get totalQuestions(): number {
    return this.questions.length;
  }

  get progressPercent(): number {
    if (!this.totalQuestions) return 0;
    return Math.round(((this.currentQuestionIndex + (this.answered ? 1 : 0)) / this.totalQuestions) * 100);
  }

  selectOption(option: string): void {
    if (!this.answered) {
      this.selectedOption = option;
    }
  }

  confirmAnswer(): void {
    if (!this.selectedOption || this.answered || !this.currentQuestion) return;
    this.isCorrect = this.selectedOption === this.currentQuestion.answer;
    if (this.isCorrect) this.score++;
    this.answered = true;
  }

  nextQuestion(): void {
    if (this.currentQuestionIndex < this.totalQuestions - 1) {
      this.currentQuestionIndex++;
      this.selectedOption = '';
      this.answered = false;
      this.isCorrect = false;
    } else {
      this.sessionFinished = true;
      this.completed.emit({ score: this.score, total: this.totalQuestions });
    }
  }

  close(): void {
    this.closed.emit();
  }

  getOptionLabel(index: number): string {
    return ['A', 'B', 'C', 'D'][index] ?? `${index + 1}`;
  }
}
