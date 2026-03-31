import { Component } from '@angular/core';
import { ExerciseService } from '../../core/services/exercise.service';

@Component({
  selector: 'app-generator',
  imports: [],
  templateUrl: './generator.component.html',
  styleUrl: './generator.component.scss'
})

export class GeneratorComponent {
  title = 'Exercise Generator';

  isLoading = false;
  errorMessage: string | null = null;
  receivedExercise: string | null = null; 
  currentTopic: string = '';

  constructor(private exerciseService: ExerciseService) {}

  generateNewExercise() {
    this.isLoading = true;
    this.errorMessage = null;
    this.receivedExercise = null;
    
    // data sent to backend
    const requestData = {
      topic: 'Past Tense Simple vs Continuous',
      category: 'grammar',
      level: 'B1',
      type: 'multiple choice',
      language: 'english' // implicit
    };

    console.log('Sending request to backend...');

    this.exerciseService.generateExercise(requestData).subscribe({
      next: (response) => {
        this.receivedExercise = response.exercise; 
        this.currentTopic = response.topic;
        this.isLoading = false;
        console.log('Exercise received successfully!');
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = 'An error occurred while communicating with the server. Please check if the backend is running.';
        console.error('Error details:', err);
      }
    });
  }
}
