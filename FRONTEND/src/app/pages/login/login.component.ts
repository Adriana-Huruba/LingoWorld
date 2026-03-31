import { Component } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

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
    email: new FormControl(' ', [Validators.required, Validators.email]), 
    password: new FormControl('', [Validators.required, Validators.minLength(6)])
  });

  login() {
    throw new Error('Method not implemented.');
  }

  redirectToRegister() {
    window.location.href= '/register';
  }
}
