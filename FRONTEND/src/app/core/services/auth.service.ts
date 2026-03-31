import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AuthService {
  isLoggedIn = signal<boolean>(false);

  setLoggedIn(status: boolean) { // will be called in backend when the user logs in
    this.isLoggedIn.set(status);
  }
}