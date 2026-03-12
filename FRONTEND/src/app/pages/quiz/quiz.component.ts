import { Component } from '@angular/core';

@Component({
  selector: 'app-quiz',
  imports: [],
  templateUrl: './quiz.component.html',
  styleUrl: './quiz.component.scss'
})

export class QuizComponent {
  currentStep: 'language' | 'level' | 'loading' | 'quiz' = 'language';
  selectedLanguage: any = null;
  selectedLevel: any = null;

  languages = [
    { id: 'en', name: 'English', flag: '🇬🇧' },
    { id: 'ro', name: 'Română', flag: '🇷🇴' },
    { id: 'fr', name: 'Francais', flag: '🇫🇷' },
    { id: 'es', name: 'Español', flag: '🇪🇸' }
  ];

  levels = [
    { id: 'A1', description: 'Beginner' },
    { id: 'A2', description: 'Elementary' },
    { id: 'B1', description: 'Intermediate' },
    { id: 'B2', description: 'Upper Intermediate' },
    { id: 'C1', description: 'Advanced' }
  ];

  selectLanguage(lang: any) {
    this.selectedLanguage = lang;
    this.currentStep = 'level';
  }

  selectLevel(lvl: any) {
    this.selectedLevel = lvl;
    this.currentStep = 'loading';
    this.generateExercises();
  }

  generateExercises() {
   
    const payload = {
      language: this.selectedLanguage.id,
      level: this.selectedLevel.id
    };
    
    console.log('Sending data to RAG:', payload);
  }
}
