import { Component, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-progress',
  imports: [],
  templateUrl: './progress.component.html',
  styleUrl: './progress.component.scss'
})
export class ProgressComponent {
  authService=inject(AuthService);

  selectedLanguage=this.authService.selectedLanguage;
}
