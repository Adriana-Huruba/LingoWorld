import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router} from '@angular/router';
import { ClassroomService } from '../../core/services/classroom.service';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzTabsModule } from 'ng-zorro-antd/tabs'; 
import { NzButtonModule } from 'ng-zorro-antd/button'; 
import { CommonModule } from '@angular/common';
import { NzSelectModule } from 'ng-zorro-antd/select';
import { FormsModule } from '@angular/forms';
import { NzInputNumberModule } from 'ng-zorro-antd/input-number';

@Component({
  selector: 'app-classroom',
  standalone: true, 
  imports: [CommonModule, NzIconModule, NzTabsModule, NzButtonModule, FormsModule, NzSelectModule, NzInputNumberModule],
  templateUrl: './classroom.component.html',
  styleUrl: './classroom.component.scss'
})

export class ClassroomComponent implements OnInit {
  private classroomService = inject(ClassroomService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  students: any[] = [];
  classroomName = '';
  inviteCode = '';
  errorMessage = '';

  activeTab: string = 'students';

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }

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

  returnToDashboard() {
    this.router.navigate(['/homepage']);
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

  topic = '';
  numberOfExercises = 10;
  focus = 'grammar';
  typesOfExercises: string[] = ['multiple_choice', 'fill-in-the-blank']; 
  
  isGenerating = false;
  isGenerated = false; // 


  generateResource() {
    if (!this.topic) 
      return;
    
    this.isGenerating = true;
      
    setTimeout(() => {
      this.isGenerating = false;
      this.isGenerated = true;
    }, 3000);
  }
}

