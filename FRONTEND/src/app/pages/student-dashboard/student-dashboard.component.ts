import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzModalModule } from 'ng-zorro-antd/modal';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzMessageService } from 'ng-zorro-antd/message';
import { AuthService } from '../../core/services/auth.service';
import { ClassroomService } from '../../core/services/classroom.service';

@Component({
  selector: 'app-student-dashboard',
  imports: [CommonModule, FormsModule, NzIconModule, NzModalModule, NzInputModule, NzButtonModule],
  templateUrl: './student-dashboard.component.html',
  styleUrl: './student-dashboard.component.scss'
})
export class StudentDashboardComponent {
  private authService = inject(AuthService);
  private classroomService = inject(ClassroomService);
  private message= inject(NzMessageService);

  student=this.authService.currentUser;
  classrooms: any[] = [];
  
  searchText = '';
  isModalVisible = false;
  inviteCode = '';

  ngOnInit(): void {
    this.loadClassrooms();
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
        this.classrooms = data.classrooms;
      },
      error: () => this.message.error('Could not load the classes.')
    });
  }

  filterText(): void {
    console.log('Filter:', this.searchText);
  }

  navigateToClassroom(id: number): void {
    console.log('Navigation to course:', id);
  }
}
