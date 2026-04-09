import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormControl, Validators, FormGroup } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss'
})

export class RegisterComponent {

  registerForm = new FormGroup({
    name: new FormControl('', [Validators.required]),
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)]),
    role: new FormControl('', [Validators.required]),
    native_language: new FormControl(''),
    target_language: new FormControl('')
  });

  constructor(private authService: AuthService, private router: Router) {}

  register() {
    if (this.registerForm.valid) {
      console.log('Data sent:', this.registerForm.value);
      this.authService.register(this.registerForm.value).subscribe({
        next: (response) => {
          alert('Account created successfully!');
          this.router.navigate(['/login']); 
        },
        error: (err) => {
          console.error('Error :', err);
          alert('Error: ' + (err.error?.detail || 'An error occurred during registration. Please try again.'));
        }
      });
    } else {
      alert('Please fill in all required fields correctly.');
    }
  }

  redirectToLogin() {
    this.router.navigate(['/login']);
  }
}
