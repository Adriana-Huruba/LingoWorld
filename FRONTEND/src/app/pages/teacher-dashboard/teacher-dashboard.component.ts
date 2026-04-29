import { Component, inject } from '@angular/core';
import { ClassroomService } from '../../core/services/classroom.service';
import { NzModalModule } from 'ng-zorro-antd/modal';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-teacher-dashboard',
  imports: [ NzModalModule, NzInputModule, NzButtonModule, FormsModule ],
  templateUrl: './teacher-dashboard.component.html',
  styleUrl: './teacher-dashboard.component.scss'
})

export class TeacherDashboardComponent {
  private classroomService = inject(ClassroomService);
  
  isModalVisible = false;
  newClassName = '';
  classrooms: any[] = [];

  ngOnInit() {
    this.loadClassrooms();
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
