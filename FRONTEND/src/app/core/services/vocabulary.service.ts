import { Injectable } from '@angular/core';

export interface VocabItem {
  id: number;
  target_word: string;
  native_word: string;
  language: string;
}

@Injectable({ providedIn: 'root' })
export class VocabularyService {
  private getStorageKey(userId: number, lang: string): string {
    return `vocab_${userId}_${lang}`;
  }

  getVocabulary(userId: number, language: string): VocabItem[] {
    const data = localStorage.getItem(this.getStorageKey(userId, language));
    return data ? JSON.parse(data) : [];
  }

  addWord(userId: number, language: string, target: string, native: string): VocabItem[] {
    const vocab = this.getVocabulary(userId, language);
    
    const newItem: VocabItem = {
      id: Date.now(),
      target_word: target,
      native_word: native,
      language: language
    };
    
    vocab.unshift(newItem); 
    localStorage.setItem(this.getStorageKey(userId, language), JSON.stringify(vocab));
    
    return vocab;
  }

  deleteWord(userId: number, language: string, wordId: number): VocabItem[] {
    let vocab = this.getVocabulary(userId, language);
    vocab = vocab.filter(w => w.id !== wordId);
    
    localStorage.setItem(this.getStorageKey(userId, language), JSON.stringify(vocab));
    return vocab;
  }
}