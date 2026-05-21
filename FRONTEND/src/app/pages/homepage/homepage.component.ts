import { Component, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { TeacherDashboardComponent } from '../teacher-dashboard/teacher-dashboard.component';
import { StudentDashboardComponent } from "../student-dashboard/student-dashboard.component";

@Component({
  selector: 'app-homepage',
  imports: [TeacherDashboardComponent, StudentDashboardComponent],
  templateUrl: './homepage.component.html',
  styleUrl: './homepage.component.scss'
})

export class HomepageComponent {
  public authService= inject(AuthService);
  
  redirectToVoiceAssistant() {
    window.location.href = '/voice-assistant';
  }

}
