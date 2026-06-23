import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { VocabularyService, VocabItem } from '../../core/services/vocabulary.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-vocabulary',
  standalone: true,
  imports: [CommonModule, FormsModule, NzIconModule],
  templateUrl: './my-vocabulary.component.html',
  styleUrl: './my-vocabulary.component.scss'
})

export class MyVocabularyComponent implements OnInit {
  authService = inject(AuthService);
  vocabService = inject(VocabularyService);

  words = signal<VocabItem[]>([]);
  newTargetWord = '';
  newNativeWord = '';

  ngOnInit() {
    this.loadWords();
  }

  loadWords() {
    const userId = this.authService.userId;
    const lang = this.authService.targetLanguageFull;
   
    this.words.set(this.vocabService.getVocabulary(userId, lang));
  }

  saveWord() {
    if (!this.newTargetWord.trim() || !this.newNativeWord.trim()) return;

    const userId = this.authService.userId;
    const lang = this.authService.targetLanguageFull;

    const updatedList = this.vocabService.addWord(
      userId,
      lang,
      this.newTargetWord.trim(),
      this.newNativeWord.trim()
    );

    this.words.set(updatedList);
    this.newTargetWord = '';
    this.newNativeWord = '';
  }

  removeWord(id: number) {
    const userId = this.authService.userId;
    const lang = this.authService.targetLanguageFull;
    
    const updatedList = this.vocabService.deleteWord(userId, lang, id);
    this.words.set(updatedList);
  }
}