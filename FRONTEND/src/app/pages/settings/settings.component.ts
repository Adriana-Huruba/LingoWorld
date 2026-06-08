import { Component, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-settings',
  imports: [],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent {
  authService=inject(AuthService);

  name = this.authService.userName;
  // email= this.authService.email; 
  targetLanguage = this.authService.targetLanguage;

}
