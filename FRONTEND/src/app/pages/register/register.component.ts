import { Component } from '@angular/core';
import { ReactiveFormsModule, FormControl, Validators, FormGroup } from '@angular/forms';

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
    language: new FormControl('', [Validators.required])
  });

  register() {
    if(this.registerForm.valid) {
      console.log('Registration successful!');
    } else {
      console.log('Please fill in all required fields correctly.');
    }
  }

  redirectToLogin() {
    window.location.href= '/login';
  }
}
