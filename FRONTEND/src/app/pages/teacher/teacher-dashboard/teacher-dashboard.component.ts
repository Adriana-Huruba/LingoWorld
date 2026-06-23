import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NzModalModule } from 'ng-zorro-antd/modal';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMessageService } from 'ng-zorro-antd/message';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ClassroomService } from '../../../core/services/classroom.service';
import { TeacherClassroom } from '../../../core/interfaces/classroom.interface';

@Component({
  selector: 'app-teacher-dashboard',
  imports: [CommonModule, NzModalModule, NzInputModule, NzButtonModule, FormsModule, NzIconModule],
  templateUrl: './teacher-dashboard.component.html',
  styleUrl: './teacher-dashboard.component.scss'
})

export class TeacherDashboardComponent {
  private authService = inject(AuthService);
  private classroomService = inject(ClassroomService);
  private message = inject(NzMessageService);
  private router = inject(Router);

  isModalVisible = false;
  newClassName = '';
  allClassrooms: TeacherClassroom[] = [];
  classrooms: TeacherClassroom[] = [];
  searchText: string = '';
  teacher = this.authService.currentUser;
  viewMode: 'grid' | 'list' = 'grid';

  ngOnInit() {
    this.loadClassrooms();
  }

  filterText() {
    const term = this.searchText.trim().toLowerCase();
    this.classrooms = term
      ? this.allClassrooms.filter(c => c.name?.toLowerCase().includes(term))
      : [...this.allClassrooms];
  }

  navigateToClassroom(classroomId: any) {
    console.log('Navigating to classroom with ID:', classroomId);

    this.router.navigate(['/classroom', classroomId]);
  }

  loadClassrooms() {
    this.classroomService.getClassroomsOfTeacher().subscribe({
      next: (data) => {
        this.allClassrooms = data.classrooms;
        this.classrooms = [...this.allClassrooms];
      },
      error: () => this.message.error('Could not load classrooms.')
    });
  }

  handleOk(): void {
    if (!this.newClassName.trim()) {
      this.message.warning('Please enter a class name!');
      return;
    }
    this.classroomService.createClassroom(this.newClassName).subscribe({
      next: (res) => {
        this.message.success(`Class created! Invite code: ${res.invite_code}`);
        this.isModalVisible = false;
        this.newClassName = '';
        this.loadClassrooms();
      },
      error: () => this.message.error('Error creating class.')
    });
  }

  handleCancel(): void {
    this.isModalVisible = false;
  }

  showModal() {
    this.isModalVisible = true;
  }
}
