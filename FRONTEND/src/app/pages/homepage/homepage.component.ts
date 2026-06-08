import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { TeacherDashboardComponent } from '../teacher-dashboard/teacher-dashboard.component';
import { StudentDashboardComponent } from "../student/student-dashboard/student-dashboard.component";
import { ExerciseService } from '../../core/services/exercise.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-homepage',
  imports: [CommonModule, TeacherDashboardComponent, StudentDashboardComponent],
  templateUrl: './homepage.component.html',
  styleUrl: './homepage.component.scss'
})

export class HomepageComponent implements OnInit {
  public authService= inject(AuthService);
  private exerciseService = inject(ExerciseService);
  private route= inject(Router);
  
  topics: string[] = [];
  ngOnInit() {
    if (this.authService.userRole() === "adult_learner") {
      this.loadTopics();
    }
  }

  loadTopics() {
    this.exerciseService.getTopics().subscribe({
      next: (data) => {
        this.topics = data;
      },
      error: (err) => {
        console.error('Error at getting the topics: ', err);
      }
    });
  }

  redirectToGenerator() {
    this.route.navigate(['/generator']);
  }

  redirectToVoiceAssistant() {
    window.location.href = '/voice-assistant';
  }

}
