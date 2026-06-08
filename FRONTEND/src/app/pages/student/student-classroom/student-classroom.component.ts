import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ClassroomService } from '../../../core/services/classroom.service';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { UniversalPlayerComponent } from '../../universal-player/universal-player.component';
import { QuizMode } from '../../../core/enums/quiz-mode.enum';

export interface AssignmentQuestion {
  question: string;
  options: string[];
  answer: string;
}

export interface Assignment {
  id: number;
  title: string;
  due_date: string;
  status: 'pending' | 'in-progress' | 'completed';
  questions: AssignmentQuestion[];
}

@Component({
  selector: 'app-student-classroom',
  imports: [CommonModule, FormsModule, NzIconModule, UniversalPlayerComponent],
  templateUrl: './student-classroom.component.html',
  styleUrl: './student-classroom.component.scss'
})

export class StudentClassroomComponent {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private classroomService = inject(ClassroomService);

  QuizMode = QuizMode;
  errorMessage = '';
  classroom: any = {};
  classroomName = '';

  showModal = false;
  assignments: Assignment[] = [];
  activeAssignment: Assignment | null = null;

  ngOnInit() {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (!idParam) { this.errorMessage = 'Missing classroom ID in route.'; return; }

    const classroomId = Number(idParam);
    if (Number.isNaN(classroomId)) { this.errorMessage = 'Invalid classroom ID.'; return; }

    this.loadClassroom(classroomId);
    this.loadAssignments(classroomId);

  }

  loadClassroom(classroomId: number) {
    this.classroomService.getClassroomById(classroomId).subscribe({
      next: (data) => { this.classroom = data; this.classroomName = data.name || ''; },
      error: () => { this.errorMessage = 'Could not load classroom details.'; }
    });
  }

  
  loadAssignments(classroomId: number) {
    this.classroomService.getClassroomAssignments(classroomId).subscribe({
      next: (data) => { this.assignments = data.assignments; },
      error: () => { this.errorMessage = 'Could not load assignments.'; }
    });
  }
   

  returnToDashboard() {
    this.router.navigate(['/homepage']);
  }

  startAssignment(assignment: Assignment): void {
    this.activeAssignment = assignment;
    this.showModal = true;
    assignment.status = 'in-progress';
  }

  closeModal(): void {
    this.showModal = false;
    this.activeAssignment = null;
  }

  onAssignmentCompleted(result: { score: number; total: number }): void {
    if (this.activeAssignment) {
      this.activeAssignment.status = 'completed';
    }
  }

  isDueSoon(dueDateStr: string): boolean {
    const due = new Date(dueDateStr);
    const now = new Date();
    const diffMs = due.getTime() - now.getTime();
    return diffMs > 0 && diffMs < 3 * 24 * 60 * 60 * 1000;
  }

  getStatusClass(status: string): string {
    return ({ 'pending': 'status-pending', 'in-progress': 'status-inprogress', 'completed': 'status-completed' }[status] ?? '');
  }

  getStatusLabel(status: string): string {
    return ({ 'pending': 'Pending', 'in-progress': 'In Progress', 'completed': 'Completed' }[status] ?? status);
  }
}
