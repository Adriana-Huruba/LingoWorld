import { Component } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCheckboxModule } from 'ng-zorro-antd/checkbox';
import { NzFormModule } from 'ng-zorro-antd/form';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzNotificationService } from 'ng-zorro-antd/notification';

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

  constructor(private authService: AuthService, private router: Router, private notification: NzNotificationService) {
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/homepage']);
    }
  }

  login() {
    if (this.loginForm.valid) 
    {
      console.log('Login data:', this.loginForm.value);

      this.authService.login(this.loginForm.value as {email: string, password: string}).subscribe({
        next: (response: any) => {
          this.authService.setSession(response.user);

          console.log('Login successful:', response);
          this.notification.success('Login successful', 'You have been logged in.', { 
            nzDuration: 2000,        
            nzPlacement: 'top',    
            nzClass: 'custom-success-notification'
          });
          
          if (response.user.role === 'teacher' || response.user.role === 'student') {
            this.router.navigate(['/homepage']);
          } else {
            // this.router.navigate(['/quiz']);
            this.router.navigate(['/homepage']);
          }
        },
        error: (err) => {
          console.error('Login error:', err);
          this.notification.error('Login failed', 'Invalid credentials', {
            nzDuration: 3000,
            nzPlacement: 'top',
            nzClass: 'custom-error-notification'
          });
        }
      });
    } 
    else {
      this.notification.warning('Invalid input','Please fill in all required fields correctly.');
    }
  }

  redirectToRegister() {
    this.router.navigate(['/register']);
  }
}
