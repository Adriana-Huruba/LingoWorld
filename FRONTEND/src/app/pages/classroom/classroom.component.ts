import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ClassroomService } from '../../core/services/classroom.service';

@Component({
  selector: 'app-classroom',
  imports: [],
  templateUrl: './classroom.component.html',
  styleUrl: './classroom.component.scss'
})

export class ClassroomComponent implements OnInit {
  private classroomService = inject(ClassroomService);
  private route = inject(ActivatedRoute);

  students: any[] = [];
  classroomName = '';
  inviteCode = '';
  errorMessage = '';

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
    this.loadStudents(classroomId);
  }

  loadClassroom(classroomId: number) {
    this.classroomService.getClassroomById(classroomId).subscribe({
      next: (data) => {
        this.classroomName = data.name || '';
        this.inviteCode = data.invite_code || data.inviteCode || '';
      },
      error: (err) => {
        console.error('Error loading classroom details', err);
        this.errorMessage = 'Could not load classroom details.';
      }
    });
  }

  loadStudents(classroomId: number) {
    this.classroomService.getClassroomStudents(classroomId).subscribe({
      next: (data) => {
        this.students = data.students || data;
      },
      error: (err) => {
        console.error('Error loading classroom students', err);
      }
    });
  }
}

