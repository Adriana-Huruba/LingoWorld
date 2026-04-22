import { Component } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCheckboxModule } from 'ng-zorro-antd/checkbox';
import { NzFormModule } from 'ng-zorro-antd/form';
import { NzInputModule } from 'ng-zorro-antd/input';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, NzButtonModule, NzCheckboxModule, NzFormModule, NzInputModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})

export class LoginComponent {
  loginForm =  new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]), 
    password: new FormControl('', [Validators.required, Validators.minLength(6)])
  });

  constructor(private authService: AuthService, private router: Router) {}

  login() {
    if (this.loginForm.valid) {
      console.log('Login data:', this.loginForm.value);
      this.authService.login(this.loginForm.value as {email: string, password: string}).subscribe({
        next: (response: any) => {
          console.log('Login successful:', response);
          if (response?.user?.target_language) {
            this.authService.updateTargetLanguage(response.user.target_language);
          }
          this.authService.setLoggedIn(true);
          alert('Login successful!'); //to do: replace with better notification
          this.router.navigate(['/quiz']);
        },
        error: (err) => {
          console.error('Login error:', err);
          alert('Login failed: ' + (err.error?.detail || 'Invalid credentials'));
        }
      });
    } else {
      alert('Please fill in all required fields correctly.');
    }
  }

  redirectToRegister() {
    this.router.navigate(['/register']);
  }
}
