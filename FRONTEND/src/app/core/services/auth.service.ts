import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Observable } from 'rxjs/internal/Observable';

export type UserRole = 'student' | 'teacher' | 'adult' | null;

@Injectable({ 
  providedIn: 'root'
})
export class AuthService {
  private languageCodeMap: { [key: string]: string } = {
    english: 'en', romanian: 'ro', spanish: 'es', french: 'fr',
    en: 'en', ro: 'ro', es: 'es', fr: 'fr',
    română: 'ro', français: 'fr', español: 'es'
  };
  
  private normalizeLanguage(language: string | null): string {
    if (!language) {
      return 'en';
    }
    return this.languageCodeMap[language.toLowerCase()] || language.toLowerCase();
  }

  user_id = signal<number>(Number(localStorage.getItem('user_id')));
  isLoggedIn = signal<boolean>(false);
  selectedLanguage = signal<string>(this.normalizeLanguage(localStorage.getItem('lang')));
  targetLanguage = signal<string>(this.normalizeLanguage(localStorage.getItem('target_lang') || localStorage.getItem('lang')));
  userRole = signal<UserRole>(localStorage.getItem('user_role') as UserRole);

  private apiUrl = 'http://localhost:8000/api'; // url from FastAPI

  constructor(private http: HttpClient) {}

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, userData);
  }

  login(credentials: {email: string, password: string}): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, credentials);
  }

  setLoggedIn(status: boolean) { // will be called in backend when the user logs in
    this.isLoggedIn.set(status);
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

  setSession(userData: any) {   
    localStorage.setItem('user_id', userData.user_id.toString());
    localStorage.setItem('token', userData.token);
    localStorage.setItem('user_role', userData.role);

    this.setLoggedIn(true);
    this.userRole.set(userData.role);
    this.user_id.set(userData.user_id);
  }

  logout() {
    this.setLoggedIn(false);
    this.userRole.set(null);
    localStorage.clear();
  }

}