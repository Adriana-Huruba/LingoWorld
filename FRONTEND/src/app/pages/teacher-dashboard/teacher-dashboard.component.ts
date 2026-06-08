import { Component, inject } from '@angular/core';
import { ClassroomService } from '../../core/services/classroom.service';
import { NzModalModule } from 'ng-zorro-antd/modal';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-teacher-dashboard',
  imports: [ NzModalModule, NzInputModule, NzButtonModule, FormsModule, NzIconModule],
  templateUrl: './teacher-dashboard.component.html',
  styleUrl: './teacher-dashboard.component.scss'
})

export class TeacherDashboardComponent {
  private authService = inject(AuthService);
  private classroomService = inject(ClassroomService);
  private router = inject(Router);
  
  isModalVisible = false;
  newClassName = '';
  classrooms: any[] = [];
  searchText: any;
  teacher = this.authService.currentUser;

  ngOnInit() {
    this.loadClassrooms();
  }

  filterText() {
    throw new Error('Method not implemented.'); //TODO: filtering by different criteria
  }

  navigateToClassroom(classroomId: any) {
    console.log('Navigating to classroom with ID:', classroomId);

    this.router.navigate(['/classroom', classroomId]);
  }

  loadClassrooms() {
    this.classroomService.getClassroomsOfTeacher().subscribe({
      next: (data) => {
        this.classrooms = data.classrooms; 
      },
      error: (err) => console.error('Error loading classrooms', err)
    });
  }

  handleOk(): void {
    if (this.newClassName.trim()) {
      this.classroomService.createClassroom(this.newClassName).subscribe({
        next: (res) => {
          console.log('Class created with code:', res.invite_code);
          this.isModalVisible = false;
          this.newClassName = '';
          this.loadClassrooms();
        },
        error: (err) => alert('Error creating class')
      });
    }
  }

  handleCancel(): void {
    this.isModalVisible = false;
  }
  
  showModal() {
    this.isModalVisible = true;
  }
}
