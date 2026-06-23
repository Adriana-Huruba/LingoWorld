import { HttpClient } from '@angular/common/http';
import { Injectable, signal, computed, effect } from '@angular/core';
import { Observable } from 'rxjs/internal/Observable';
import {User} from '../interfaces/user.interface';

export type UserRole = 'student' | 'teacher' | 'adult_learner' | null;

@Injectable({ 
  providedIn: 'root'
})

export class AuthService {
  private languageCodeMap: { [key: string]: string } = {
    english: 'en', romanian: 'ro', spanish: 'es', french: 'fr',
    en: 'en', ro: 'ro', es: 'es', fr: 'fr',
    română: 'ro', français: 'fr', español: 'es'
  };

  private codeToFullMap: { [key: string]: string } = {
    en: 'english', ro: 'romanian', es: 'spanish', fr: 'french'
  };
  
  private apiUrl = 'http://localhost:8000/api';
  currentUser = signal<User | null>(this.getUserFromStorage());

  isLoggedIn = computed(() => !!this.currentUser());
  currentUserId = computed(() => this.currentUser()?.id ?? 0);
  userRole = computed(() => this.currentUser()?.role ?? null);
  userName = computed(() => this.currentUser()?.name ?? '');

  selectedLanguage = signal<string>(this.normalizeLanguage(localStorage.getItem('lang')));
  targetLanguage = signal<string>(this.normalizeLanguage(localStorage.getItem('target_lang') || localStorage.getItem('lang')));
  userXp = signal<number>(Number(localStorage.getItem('user_xp')) || 0);
  userElo = signal<number>(Number(localStorage.getItem('user_elo')) || 0);

  constructor(private http: HttpClient) {
    effect(() => {
      localStorage.setItem('user_xp', this.userXp().toString());
      localStorage.setItem('user_elo', this.userElo().toString());
    });
  }

  normalizeLanguage(language: string | null): string {
    if (!language) 
      return 'en';
    return this.languageCodeMap[language.toLowerCase()] || language.toLowerCase();
  }

  private getUserFromStorage(): User | null {
    const userId = localStorage.getItem('user_id');
    if (!userId) 
      return null;

    return {
      id: Number(userId),
      name: localStorage.getItem('user_name') || '',
      email: localStorage.getItem('user_email') || '',
      role: localStorage.getItem('user_role') as any,
      language: localStorage.getItem('lang') as any || 'english',
      level: localStorage.getItem('user_level') || undefined
    };
  }

  get userId(): number{
    return this.currentUserId();
  }
  
  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, userData);
  }

  login(credentials: {email: string, password: string}): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, credentials);
  }
  
  setSession(userData: any) {
    localStorage.setItem('user_id', userData.user_id.toString());
    localStorage.setItem('token', userData.token);
    localStorage.setItem('user_role', userData.role);
    localStorage.setItem('user_name', userData.name);
    if (userData.email)
      localStorage.setItem('user_email', userData.email);
    if (userData.target_language) {
      const normalizedTarget = this.normalizeLanguage(userData.target_language);
      localStorage.setItem('target_lang', normalizedTarget);
      localStorage.setItem('target_lang_full', userData.target_language);
      this.targetLanguage.set(normalizedTarget);
    }
    if (userData.native_language)
      localStorage.setItem('native_lang', userData.native_language);
    if (userData.level)
      localStorage.setItem('user_level', userData.level);

    this.currentUser.set({
      id: userData.user_id,
      name: userData.name,
      email: userData.email || '',
      role: userData.role,
      language: (userData.target_language as any) || 'english',
      level: userData.level
    });
  }

  get targetLanguageFull(): string {
    const full = localStorage.getItem('target_lang_full');
    if (full) return full.toLowerCase();
    const code = localStorage.getItem('target_lang') || localStorage.getItem('lang');
    if (code) return this.codeToFullMap[code.toLowerCase()] || code.toLowerCase();
    return 'english';
  }

  get userLevel(): string {
    return localStorage.getItem('user_level') || 'B1';
  }

  get nativeLanguageFull(): string {
    const full = localStorage.getItem('native_lang');
    if (full) return full.toLowerCase();
    const targetCode = localStorage.getItem('target_lang') || 'en';
    return targetCode === 'ro' ? 'english' : 'romanian';
  }

  logout() {
    localStorage.clear();
    this.currentUser.set(null);
    this.userXp.set(0);
    this.userElo.set(0);
  }

  updateLanguage(language: string) {
    const normalized = this.normalizeLanguage(language);
    this.selectedLanguage.set(normalized);
    this.targetLanguage.set(normalized);
    localStorage.setItem('lang', normalized);
    localStorage.setItem('target_lang', normalized);
  }

  updateTargetLanguage(language: string) {
    const normalized = this.normalizeLanguage(language);
    this.targetLanguage.set(normalized);
    localStorage.setItem('target_lang', normalized);
  }

  updateLevel(cefr: string): void {
    if (!cefr) return;
    localStorage.setItem('user_level', cefr);
    const current = this.currentUser();
    if (current) {
      this.currentUser.set({ ...current, level: cefr });
    }
  }

  updateElo(elo: number): void {
    this.userElo.set(elo);
  }
}