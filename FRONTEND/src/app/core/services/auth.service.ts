import { HttpClient } from '@angular/common/http';
import { Injectable, signal, computed } from '@angular/core';
import { Observable } from 'rxjs/internal/Observable';
import {User} from '../interfaces/user.interface';

export type UserRole = 'student' | 'teacher' | 'adult-learner' | null;

@Injectable({ 
  providedIn: 'root'
})

export class AuthService {
  private languageCodeMap: { [key: string]: string } = {
    english: 'en', romanian: 'ro', spanish: 'es', french: 'fr',
    en: 'en', ro: 'ro', es: 'es', fr: 'fr',
    română: 'ro', français: 'fr', español: 'es'
  };
  
  private apiUrl = 'http://localhost:8000/api'; // url from FastAPI
  currentUser = signal<User | null>(this.getUserFromStorage());

  isLoggedIn = computed(() => !!this.currentUser());
  currentUserId = computed(() => this.currentUser()?.id ?? 0);
  userRole = computed(() => this.currentUser()?.role ?? null);
  userName = computed(() => this.currentUser()?.name ?? '');

  selectedLanguage = signal<string>(this.normalizeLanguage(localStorage.getItem('lang')));
  targetLanguage = signal<string>(this.normalizeLanguage(localStorage.getItem('target_lang') || localStorage.getItem('lang')));

  constructor(private http: HttpClient) {}

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
    if(userData.email) 
      localStorage.setItem('user_email', userData.email);

    this.currentUser.set({
      id: userData.user_id,
      name: userData.name,
      email: userData.email || '',
      role: userData.role,
      language: (userData.language as any) || 'english',
      level: userData.level
    });
  }

  logout() {
    localStorage.clear();
    this.currentUser.set(null);
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
}