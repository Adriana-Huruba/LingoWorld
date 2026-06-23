import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ClassroomService } from '../../../core/services/classroom.service';
import { AuthService } from '../../../core/services/auth.service';
import { ClassroomStudent } from '../../../core/interfaces/classroom.interface';
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
  due_date: string | null;
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
  authService = inject(AuthService);

  QuizMode = QuizMode;
  errorMessage = '';
  classroom: any = {};
  classroomName = '';

  showModal = false;
  assignments: Assignment[] = [];
  activeAssignment: Assignment | null = null;
  rankingStudents: ClassroomStudent[] = [];

  ngOnInit() {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (!idParam) { this.errorMessage = 'Missing classroom ID in route.'; return; }

    const classroomId = Number(idParam);
    if (Number.isNaN(classroomId)) { this.errorMessage = 'Invalid classroom ID.'; return; }

    this.loadClassroom(classroomId);
    this.loadAssignments(classroomId);
    this.loadRanking(classroomId);

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
   

  loadRanking(classroomId: number) {
    this.classroomService.getClassroomStudents(classroomId).subscribe({
      next: (data) => {
        this.rankingStudents = [...data.students].sort((a, b) => b.elo_score - a.elo_score);
      },
      error: () => {}
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
    if (!this.activeAssignment) return;

    this.activeAssignment.status = 'completed';

    // Persist completion so teacher and recommender system can see it
    const worksheetId = this.activeAssignment.id;
    const studentId   = this.authService.userId;

    this.classroomService.completeWorksheet(studentId, worksheetId, result.score, result.total)
      .subscribe({
        next: () => console.log(`[Student] Worksheet ${worksheetId} marked complete — ${result.score}/${result.total}`),
        error: (err) => console.warn('[Student] Could not save worksheet completion:', err),
      });
  }

  isDueSoon(dueDateStr: string | null): boolean {
    if (!dueDateStr) return false;
    const due = new Date(dueDateStr);
    const now = new Date();
    const diffMs = due.getTime() - now.getTime();
    return diffMs > 0 && diffMs < 3 * 24 * 60 * 60 * 1000; // within 3 days
  }

  isOverdue(dueDateStr: string | null): boolean {
    if (!dueDateStr) return false;
    return new Date(dueDateStr) < new Date();
  }

  getStatusClass(status: Assignment['status']): string {
    return {
      'pending': 'status-pending',
      'in-progress': 'status-in-progress',
      'completed': 'status-completed',
    }[status] ?? '';
  }

  getStatusLabel(status: Assignment['status']): string {
    return {
      'pending': 'Pending',
      'in-progress': 'In Progress',
      'completed': 'Completed',
    }[status] ?? status;
  }
}
