import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ClassroomService } from '../../../core/services/classroom.service';
import { NzIconModule } from 'ng-zorro-antd/icon';

@Component({
  selector: 'app-student-classroom',
  imports: [CommonModule, NzIconModule],
  templateUrl: './student-classroom.component.html',
  styleUrl: './student-classroom.component.scss'
})

export class StudentClassroomComponent {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private classroomService = inject(ClassroomService);

  errorMessage = '';
  classroom: any ={};
  classroomName = '';
  

  ngOnInit() {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (!idParam) {
      this.errorMessage = 'Missing classroom ID in route.';
      return;
    }

    const classroomId = Number(idParam);
    if (Number.isNaN(classroomId)) {
      this.errorMessage = 'Invalid classroom ID.';
      return;
    }

    this.loadClassroom(classroomId);
    // this.loadStudents(classroomId); //for colleagues
  }

  loadClassroom(classroomId: number) {
    this.classroomService.getClassroomById(classroomId).subscribe({
      next: (data) => {
        this.classroom = data;
        this.classroomName = data.name || '';
      },
      error: (err) => {
        console.error('Error loading classroom details', err);
        this.errorMessage = 'Could not load classroom details.';
      }
    });
  }

  returnToDashboard() {
    this.router.navigate(['/homepage']);
  }

}
