import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ExerciseService } from '../../core/services/exercise.service';
import { AuthService } from '../../core/services/auth.service';

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
  reason?: string;
}

@Component({
  selector: 'app-generator',
  imports: [CommonModule, FormsModule], 
  templateUrl: './generator.component.html',
  styleUrl: './generator.component.scss'
})

export class GeneratorComponent {
  authService=inject(AuthService);
  title = 'Exercise Generator';

  isLoading = false;
  errorMessage: string | null = null;

  receivedExercise: ExerciseResponse | null = null; 
  selectedOption: string = '';
  usedHint: boolean = false;
  submitMessage: string | null = null;
  isAnswerCorrect: boolean | null = null;
  startTime: number = 0; //time of response

  history: Array<{ exId: number; correct: boolean; oldElo: number; newElo: number; reason?: string }> = [];

  constructor(private exerciseService: ExerciseService) {}

  generateNewExercise() {
    this.isLoading = true;
    this.errorMessage = null;
    this.receivedExercise = null;
    this.selectedOption = '';
    this.usedHint = false;
    this.submitMessage = null;
    this.isAnswerCorrect = null; 
  
    console.log('Sending request to backend...');

    this.exerciseService.getNextExercise({user_id : this.authService.currentUserId(), target_language: 'english'}).subscribe({
      next: (response) => {
        this.receivedExercise = response;
        this.startTime = Date.now();
        this.isLoading = false;
        console.log('Recommended exercise:', response);
        console.log('Reason (branch):', response.reason || 'not specified');
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Error at request of exercices';
        console.error(err);
      }
    });
  }

  useHint() {
    this.usedHint = true;
    //TO DO: logic for generating + showing the hint
  }

  submitAnswer() {
    if (!this.receivedExercise) 
      return;
    if (!this.selectedOption) {
      this.submitMessage = "Choose an option!";
      return;
    }
    
    const timeTaken = Math.floor((Date.now() - this.startTime) / 1000);
    this.isAnswerCorrect = this.selectedOption === this.receivedExercise.correct_answer;

    const payload = {
      user_id : this.authService.currentUserId(),
      exercise_id: this.receivedExercise.exercise_id,
      is_correct: this.isAnswerCorrect,
      response_time_seconds: timeTaken,
      exercise_type: this.receivedExercise.type,
      used_hint: this.usedHint
    };
    
    this.exerciseService.submitAnswer(payload).subscribe({
      next: (result) => {
        this.history.push({
          exId: this.receivedExercise!.exercise_id,
          correct: this.isAnswerCorrect!,
          oldElo: result.old_elo,
          newElo: result.new_elo,
          reason: this.receivedExercise!.reason
        });

        if (this.isAnswerCorrect) {
          this.submitMessage = `Correct! ELO: ${result.old_elo} → ${result.new_elo} (${result.delta_elo > 0 ? '+' : ''}${result.delta_elo}) | Quality: ${result.quality} | Next review: ${result.new_interval} day(s)`;
        } else {
          this.submitMessage = `Wrong! Right answer: ${this.receivedExercise!.correct_answer}. ELO: ${result.old_elo} → ${result.new_elo} (${result.delta_elo})`;
        }
        console.log('Submit response:', result);
      },
      error: (err) => {
        this.submitMessage = 'Error at sending the response';
        console.error(err);
      }
    });
  }
}