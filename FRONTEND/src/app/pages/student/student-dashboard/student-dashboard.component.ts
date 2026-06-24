import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzModalModule } from 'ng-zorro-antd/modal';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzMessageService } from 'ng-zorro-antd/message';
import { AuthService } from '../../../core/services/auth.service';
import { ClassroomService } from '../../../core/services/classroom.service';
import { StudentClassroom } from '../../../core/interfaces/classroom.interface';

@Component({
  selector: 'app-student-dashboard',
  imports: [CommonModule, FormsModule, NzIconModule, NzModalModule, NzInputModule, NzButtonModule],
  templateUrl: './student-dashboard.component.html',
  styleUrl: './student-dashboard.component.scss'
})
export class StudentDashboardComponent {
  private authService = inject(AuthService);
  private classroomService = inject(ClassroomService);
  private message = inject(NzMessageService);
  private router = inject(Router);

  student = this.authService.currentUser;
  allClassrooms: StudentClassroom[] = [];
  classrooms: StudentClassroom[] = [];
  pendingAssignments: any[] = [];

  searchText = '';
  isModalVisible = false;
  inviteCode = '';
  viewMode: 'grid' | 'list' = 'grid';

  ngOnInit(): void {
    this.loadClassrooms();
    this.loadPendingAssignments();
  }

  loadPendingAssignments(): void {
    const studentId = this.authService.userId;
    this.classroomService.getPendingAssignmentsForStudent(studentId).subscribe({
      next: (data) => { this.pendingAssignments = data.assignments; },
      error: () => {}
    });
  }

  navigateToAssignment(assignment: any): void {
    // Navigate to classroom so student can start the assignment
    this.router.navigate(['/class', assignment.classroom_id ?? assignment.id]);
  }

  enrollIn(): void {
    this.isModalVisible = true;
    this.inviteCode = ''; 
  }

  handleCancel(): void {
    this.isModalVisible = false;
  }

  handleOk(): void {
    if (!this.inviteCode || this.inviteCode.trim() === '') {
      this.message.warning('Please enter a code!');
      return;
    }

    const studentId = this.authService.userId;

    this.classroomService.enrollStudent(studentId, this.inviteCode.trim()).subscribe({
      next: (response) => {
        this.message.success(response.message || 'You are enrolled!');
        this.isModalVisible = false;
        
        this.loadClassrooms();
      },
      error: (err) => {
        const errorMessage = err.error?.detail || 'Error at enrolling';
        this.message.error(errorMessage);
      }
    });
  }

  loadClassrooms(): void {
    const studentId = this.authService.userId;
    this.classroomService.getStudentClassrooms(studentId).subscribe({
      next: (data) => {
        this.allClassrooms = data.classrooms;
        this.classrooms = [...this.allClassrooms];
      },
      error: () => this.message.error('Could not load the classes.')
    });
  }

  filterText(): void {
    const term = this.searchText.trim().toLowerCase();
    this.classrooms = term
      ? this.allClassrooms.filter(c => c.name?.toLowerCase().includes(term))
      : [...this.allClassrooms];
  }

  navigateToClassroom(id: number): void {
    this.router.navigate(['/class', id]);
  }
}
