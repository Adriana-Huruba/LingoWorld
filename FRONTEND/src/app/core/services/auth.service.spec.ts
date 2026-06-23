/// <reference types="jasmine" />

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AuthService],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('register() trimite POST la /api/register cu datele utilizatorului', () => {
    const payload = { name: 'Ion', email: 'ion@test.ro', password: 'parola123', role: 'student' };
    service.register(payload).subscribe();

    const req = httpMock.expectOne('http://localhost:8000/api/register');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ user_id: 5, token: 'abc' });
  });

  it('register() returneaza eroare când emailul este deja folosit', () => {
    let errorReceived = false;
    service.register({ email: 'existent@test.ro', password: 'x' }).subscribe({
      error: () => { errorReceived = true; }
    });

    const req = httpMock.expectOne('http://localhost:8000/api/register');
    req.flush({ detail: 'Email already registered' }, { status: 409, statusText: 'Conflict' });
    expect(errorReceived).toBeTrue();
  });

  it('login() trimite POST la /api/login cu credentialele corecte', () => {
    const credentials = { email: 'ion@test.ro', password: 'parola123' };
    service.login(credentials).subscribe();

    const req = httpMock.expectOne('http://localhost:8000/api/login');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(credentials);
    req.flush({ user_id: 1, token: 'tok', role: 'student', name: 'Ion' });
  });

  it('login() returneaza eroare 401 cand credentialele sunt gresite', () => {
    let statusCode = 0;
    service.login({ email: 'gresit@test.ro', password: 'gresit' }).subscribe({
      error: (err) => { statusCode = err.status; }
    });

    const req = httpMock.expectOne('http://localhost:8000/api/login');
    req.flush({ detail: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });
    expect(statusCode).toBe(401);
  });

  it('setSession() actualizeaza semnalul currentUser si salveaza in localStorage', () => {
    service.setSession({
      user_id: 7, token: 'tok7', role: 'teacher', name: 'Maria',
      email: 'maria@test.ro', target_language: 'english', native_language: 'romanian', level: 'B2',
    });

    expect(service.isLoggedIn()).toBeTrue();
    expect(service.currentUserId()).toBe(7);
    expect(service.userRole()).toBe('teacher');
    expect(service.userName()).toBe('Maria');
    expect(localStorage.getItem('user_id')).toBe('7');
    expect(localStorage.getItem('token')).toBe('tok7');
    expect(localStorage.getItem('user_level')).toBe('B2');
  });

  it('isLoggedIn() returneaza false inainte de autentificare', () => {
    expect(service.isLoggedIn()).toBeFalse();
  });


  it('logout() sterge sesiunea din localStorage si reseteaza semnalul', () => {
    service.setSession({ user_id: 3, token: 't', role: 'student', name: 'X', email: '' });
    expect(service.isLoggedIn()).toBeTrue();

    service.logout();

    expect(service.isLoggedIn()).toBeFalse();
    expect(service.currentUser()).toBeNull();
    expect(localStorage.getItem('user_id')).toBeNull();
  });


  it('normalizeLanguage() converteste nume complete la coduri', () => {
    expect(service.normalizeLanguage('english')).toBe('en');
    expect(service.normalizeLanguage('romanian')).toBe('ro');
    expect(service.normalizeLanguage('french')).toBe('fr');
    expect(service.normalizeLanguage('español')).toBe('es');
  });

  it('normalizeLanguage() accepta si coduri deja normalizate', () => {
    expect(service.normalizeLanguage('en')).toBe('en');
    expect(service.normalizeLanguage('ro')).toBe('ro');
  });

  it('normalizeLanguage() returneaza "en" pentru valoarea null', () => {
    expect(service.normalizeLanguage(null)).toBe('en');
  });
});
