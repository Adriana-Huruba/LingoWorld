import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Observable } from 'rxjs/internal/Observable';

@Injectable({ 
  providedIn: 'root'
})
export class AuthService {
  isLoggedIn = signal<boolean>(false);

  setLoggedIn(status: boolean) { // will be called in backend when the user logs in
    this.isLoggedIn.set(status);
  }
  private apiUrl = 'http://localhost:8000/api'; // url from FastAPI

  constructor(private http: HttpClient) {}

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, userData);
  }

  login(credentials: {email: string, password: string}): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, credentials);
  }
}