import { Component, OnInit, Input, Output, EventEmitter, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { QuizMode } from '../../core/enums/quiz-mode.enum';
import { ExerciseService } from '../../core/services/exercise.service';
import { AuthService } from '../../core/services/auth.service';
import { VocabularyService } from '../../core/services/vocabulary.service';

export interface PlayerQuestion {
  exercise_id?: number;
  type: 'multiple-choice' | 'fill-in-the-blank' | 'translation' | 'match';
  exercise_title: string;
  question?: string;
  base_sentence?: string;
  options?: string[];
  answer?: string;
  pairs?: Array<{ target: string; native: string }>;
  level?: string;
  language?: string;
  topic?: string;
}

@Component({
  selector: 'app-universal-player',
  standalone: true,
  imports: [CommonModule, FormsModule, NzIconModule],
  templateUrl: './universal-player.component.html',
  styleUrl: './universal-player.component.scss'
})

export class UniversalPlayerComponent implements OnInit, OnChanges {
  @Input() mode!: QuizMode;
  @Input() title: string = '';
  @Input() topicContext?: string;
  @Input() assignmentId?: number;
  @Input() preloadedExercises?: any[];

  @Output() closed = new EventEmitter<void>();
  @Output() completed = new EventEmitter<{
    score: number;
    total: number;
    responses?: Array<{ exercise_id: number; level: string; is_correct: boolean }>;
  }>();

  private exerciseService = inject(ExerciseService);
  authService = inject(AuthService);
  private vocabService = inject(VocabularyService);

  public QuizMode = QuizMode;

  questions: PlayerQuestion[] = [];
  currentQuestionIndex = 0;
  answered = false;
  isCorrect = false;
  score = 0;
  sessionFinished = false;
  usedHint = false;
  hint: string | null = null;
  hintLoading = false;

  selectedOption = '';
  textAnswer = '';

  private quizResponses: Array<{ exercise_id: number; level: string; is_correct: boolean }> = [];

  shuffledNatives: string[] = [];
  selectedTarget: string | null = null;
  selectedNative: string | null = null;
  userPairs: Array<{ target: string; native: string }> = [];
  feedbackData: any = null;
  matchFeedback: 'correct' | 'wrong' | null = null;

  showVocabForm = false;
  vocabTarget = '';
  vocabNative = '';
  vocabSuccess = false;

  private questionStartTime = 0;

  ngOnInit(): void {
    if (this.preloadedExercises?.length) {
      this.questions = this.normalizeQuestions(this.preloadedExercises);
      this.startTimer();
      if (this.questions[0]?.type === 'match') this.initMatch();
    }
  }

  private startTimer(): void { this.questionStartTime = Date.now(); }
  private elapsedSeconds(): number { return Math.round((Date.now() - this.questionStartTime) / 1000); }

  private normalizeQuestions(raw: any[]): PlayerQuestion[] {
    const seen = new Set<number>();
    const result: PlayerQuestion[] = [];

    for (const item of raw) {
      if (!item) continue;

      if (item.exercise_id && seen.has(item.exercise_id)) continue;
      if (item.exercise_id) seen.add(item.exercise_id);

      if (item.type && !item.content) {
        result.push(item as PlayerQuestion);
        continue;
      }

      const exId: number | undefined = item.exercise_id ?? undefined;
      const rawType: string = (item.type ?? '').toLowerCase();
      const content = item.content ?? {};

      const itemLevel: string = item.level ?? '';

      // match
      if (rawType === 'match' || rawType === 'matching' || content.pairs) {
        result.push({
          exercise_id: exId,
          type: 'match',
          exercise_title: content.exercise_title ?? '',
          pairs: content.pairs ?? [],
          answer: item.correct_answer ?? item.answer ?? '',
          level: itemLevel,
        });
        continue;
      }

      if (rawType === 'multiple-choice') {
        const firstQ = content.questions?.[0];
        result.push({
          exercise_id: exId,
          type: 'multiple-choice',
          exercise_title: content.exercise_title ?? '',
          question: firstQ?.question ?? content.question ?? item.question ?? '',
          options: firstQ?.options ?? content.options ?? item.options ?? [],
          answer: item.correct_answer ?? firstQ?.answer ?? item.answer ?? '',
          level: itemLevel,
        });
        continue;
      }

      // translation / fill-in-the-blank
      if (rawType === 'translation' || rawType === 'fill-in-the-blank' || rawType === 'fill_in_the_blank' || content.base_sentence) {
        const firstQ = content.questions?.[0];
        result.push({
          exercise_id: exId,
          type: rawType === 'translation' ? 'translation' : 'fill-in-the-blank',
          exercise_title: content.exercise_title ?? '',
          base_sentence: content.base_sentence ?? firstQ?.question ?? content.question ?? '',
          question: firstQ?.question ?? content.question ?? item.question ?? '',
          answer: item.correct_answer ?? item.answer ?? firstQ?.answer ?? '',
          options: [],
          level: itemLevel,
        });
        continue;
      }

      // multiple-choice flat fallback (unknown rawType, no base_sentence)
      if (item.question !== undefined || content.question !== undefined) {
        result.push({
          exercise_id: exId,
          type: 'multiple-choice',
          exercise_title: content.exercise_title ?? '',
          question: item.question ?? content.question ?? '',
          options: item.options ?? content.options ?? [],
          answer: item.correct_answer ?? item.answer ?? '',
          level: itemLevel,
        });
        continue;
      }

      result.push(item as PlayerQuestion);
    }

    return result;
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
  getOptionLabel(i: number): string { return ['A', 'B', 'C', 'D'][i] ?? String(i + 1); }

  private normalizeText(s: string): string {
    const contractions: Record<string, string> = {
      "aren't": 'are not', "isn't": 'is not', "wasn't": 'was not', "weren't": 'were not',
      "don't": 'do not', "doesn't": 'does not', "didn't": 'did not',
      "can't": 'cannot', "couldn't": 'could not', "won't": 'will not', "wouldn't": 'would not',
      "haven't": 'have not', "hasn't": 'has not', "hadn't": 'had not',
      "i'm": 'i am', "i've": 'i have', "i'll": 'i will', "i'd": 'i would',
      "he's": 'he is', "she's": 'she is', "it's": 'it is', "that's": 'that is',
      "they're": 'they are', "we're": 'we are', "you're": 'you are',
      "they've": 'they have', "we've": 'we have', "you've": 'you have',
      "they'll": 'they will', "we'll": 'we will', "you'll": 'you will',
    };
    let normalized = s.trim().toLowerCase();
    for (const [contraction, expanded] of Object.entries(contractions)) {
      normalized = normalized.replace(new RegExp(contraction.replace("'", "[''`]"), 'g'), expanded);
    }
    return normalized.replace(/[.,!?;:'"(){}\[\]]/g, '').replace(/\s+/g, ' ').trim();
  }

  private similarityRatio(a: string, b: string): number {
    if (a === b) return 1;
    const longer = a.length > b.length ? a : b;
    const shorter = a.length > b.length ? b : a;
    if (longer.length === 0) return 1;
    const editDist = this.levenshtein(longer, shorter);
    return (longer.length - editDist) / longer.length;
  }

  private levenshtein(a: string, b: string): number { //be?
    const dp: number[][] = Array.from({ length: a.length + 1 }, (_, i) =>
      Array.from({ length: b.length + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
    );
    for (let i = 1; i <= a.length; i++)
      for (let j = 1; j <= b.length; j++)
        dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1]
          : 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
    return dp[a.length][b.length];
  }

  private isAnswerCorrect(userAnswer: string, expected: string, isTranslation = false): boolean {
    const u = this.normalizeText(userAnswer);
    const e = this.normalizeText(expected);
    if (u === e) 
      return true;
    if (isTranslation) 
      return this.similarityRatio(u, e) >= 0.85;
    return false;
  }

  selectOption(option: string): void { if (!this.answered) this.selectedOption = option; }
  confirmMultipleChoice(): void {
    if (!this.selectedOption || this.answered || !this.currentQuestion) return;
    this.isCorrect = this.selectedOption.trim().toLowerCase() === this.currentQuestion.answer?.trim().toLowerCase();
    if (this.isCorrect) this.score++;
    this.answered = true;
    this.recordAnswer(this.isCorrect);
  }

  confirmTextAnswer(): void {
    if (!this.textAnswer.trim() || this.answered || !this.currentQuestion) return;
    const isTranslation = this.currentQuestion.type === 'translation';
    this.isCorrect = this.isAnswerCorrect(this.textAnswer, this.currentQuestion.answer ?? '', isTranslation);
    if (this.isCorrect) this.score++;
    this.answered = true;
    this.recordAnswer(this.isCorrect);
  }

  initMatch(): void {
    const q = this.currentQuestion;
    if (!q?.pairs) return;
    this.shuffledNatives = this.shuffle(q.pairs.map(p => p.native));
    this.userPairs = [];
    this.selectedTarget = null;
    this.selectedNative = null;
    this.matchFeedback = null;
  }

  private shuffle<T>(arr: T[]): T[] {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  isTargetMatched(t: string): boolean { 
    return this.userPairs.some(p => p.target === t); 
  }

  isNativeMatched(n: string): boolean { 
    return this.userPairs.some(p => p.native === n); 
  }

  selectTarget(target: string): void {
    if (this.answered || this.isTargetMatched(target)) 
      return;
    this.selectedTarget = target;
    this.tryPair();
  }

  selectNative(native: string): void {
    if (this.answered || this.isNativeMatched(native)) 
      return;
    this.selectedNative = native;
    this.tryPair();
  }

  private tryPair(): void {
    if (!this.selectedTarget || !this.selectedNative) 
      return;
    this.userPairs.push({ target: this.selectedTarget, native: this.selectedNative });
    this.selectedTarget = null;
    this.selectedNative = null;
  }

  undoLastPair(): void { this.userPairs.pop(); this.matchFeedback = null; }

  get allPairsMatched(): boolean {
    return !!this.currentQuestion?.pairs && this.userPairs.length === this.currentQuestion.pairs.length;
  }

  confirmMatch(): void {
    if (!this.currentQuestion?.pairs || this.answered) 
      return;

    const correctMap = new Map(this.currentQuestion.pairs.map(p => [p.target, p.native]));
    this.isCorrect = this.userPairs.every(p => correctMap.get(p.target) === p.native);

    if (this.isCorrect) 
      this.score++;
    this.matchFeedback = this.isCorrect ? 'correct' : 'wrong';
    this.answered = true;
    this.recordAnswer(this.isCorrect);
  }

  isPairCorrect(pair: { target: string; native: string }): boolean {
    return this.currentQuestion?.pairs?.some(p => p.target === pair.target && p.native === pair.native) ?? false;
  }

  getCorrectNativeFor(target: string): string {
    return this.currentQuestion?.pairs?.find(p => p.target === target)?.native ?? '';
  }

  private recordAnswer(correct: boolean): void {
    const q = this.currentQuestion;
    if (!q?.exercise_id) return;

    // In INITIAL_QUIZ mode collect responses locally — submitAnswer would incorrectly
    // update ELO/SM-2 scores before the quiz determines the starting level.
    if (this.mode === QuizMode.INITIAL_QUIZ) {
      this.quizResponses.push({
        exercise_id: q.exercise_id,
        level: q.level || 'A1',
        is_correct: correct,
      });
      return;
    }

    if (!this.authService.userId) return;

    this.exerciseService.submitAnswer({
      user_id: this.authService.userId,
      exercise_id: q.exercise_id,
      is_correct: correct,
      response_time_seconds: this.elapsedSeconds(),
      exercise_type: q.type,
      used_hint: this.usedHint,
      assignment_id: this.assignmentId
    }).subscribe({
      next: (result) => {
        this.feedbackData = {
          oldElo: result.old_elo,
          newElo: result.new_elo,
          deltaElo: result.delta_elo,
          quality: result.quality,
          nextInterval: result.new_interval
        };
        // Keep localStorage in sync so topic filtering always uses the current level
        if (result.new_elo != null) this.authService.updateElo(result.new_elo);
        if (result.new_cefr)       this.authService.updateLevel(result.new_cefr);
      },
      error: (err) => { console.warn('[Player] submitAnswer failed (non-blocking):', err); }
    });
  }

  nextQuestion(): void {
    if (this.currentQuestionIndex < this.totalQuestions - 1) {
      this.currentQuestionIndex++;
      this.resetState();
      this.startTimer();
      if (this.currentQuestion?.type === 'match') this.initMatch();
    } else {
      this.sessionFinished = true;
      this.completed.emit({
        score: this.score,
        total: this.totalQuestions,
        ...(this.mode === QuizMode.INITIAL_QUIZ ? { responses: this.quizResponses } : {}),
      });
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['preloadedExercises'] && this.preloadedExercises) {
      this.questions = this.normalizeQuestions(this.preloadedExercises);
    }
  }

  private resetState(): void {
    this.selectedOption = '';
    this.textAnswer = '';
    this.answered = false;
    this.isCorrect = false;
    this.userPairs = [];
    this.selectedTarget = null;
    this.selectedNative = null;
    this.matchFeedback = null;
    this.usedHint = false;
    this.hint = null;
    this.hintLoading = false;
    this.feedbackData = false;
  }

  useHint() {
    const q = this.currentQuestion;
    if (!q || !q.exercise_id || this.usedHint) return;
    this.usedHint = true;
    this.hintLoading = true;

    this.exerciseService.getHint({
      exercise_id: q.exercise_id,
      exercise_type: q.type,
      language: q.language || this.authService.targetLanguageFull,
      level: q.level || this.authService.userLevel,
    }).subscribe({
      next: (res) => { this.hint = res.hint; this.hintLoading = false; },
      error: () => { this.hint = 'Could not load hint.'; this.hintLoading = false; }
    });
  }

  toggleVocabForm() {
    this.showVocabForm = !this.showVocabForm;
    this.vocabSuccess = false;
  }

  onTextSelect() {
    if (this.currentQuestion?.type !== 'translation') {
      return; 
    }

    const selection = window.getSelection();
    const text = selection?.toString().trim();
    
    if (text && text.length > 1) {
      this.vocabTarget = text;      
      this.showVocabForm = true;    
    }
  }

  saveToVocab() {
    if (!this.vocabTarget.trim() || !this.vocabNative.trim()) return;
    
    this.vocabService.addWord(
      this.authService.userId!,
      this.authService.targetLanguageFull,
      this.vocabTarget.trim(),
      this.vocabNative.trim()
    );

    this.vocabTarget = '';
    this.vocabNative = '';
    this.vocabSuccess = true;

    setTimeout(() => {
      this.showVocabForm = false;
      this.vocabSuccess = false;
    }, 2000);
  }


  close(): void { 
    this.closed.emit(); 
  }
}
