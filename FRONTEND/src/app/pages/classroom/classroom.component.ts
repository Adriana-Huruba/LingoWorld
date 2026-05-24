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
import { NzMessageService } from 'ng-zorro-antd/message';

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
  private message = inject(NzMessageService);

  students: any[] = [];
  classroomName = '';
  inviteCode = '';
  errorMessage = '';
  selectedFile: File | null = null;
  isDragging = false;

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

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.validateAndSetFile(input.files[0]);
      input.value = ''; 
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.validateAndSetFile(event.dataTransfer.files[0]);
    }
  }

  validateAndSetFile(file: File) {
    if (file.type !== 'application/pdf') {
      this.message.error('You can only upload files in PDF format!');
      return;
    }

    const maxSizeInMB = 10; //limit 
    if (file.size > maxSizeInMB * 1024 * 1024) {
      this.message.warning(`The uploaded file is too big, the limit is ${maxSizeInMB}MB!`);
      return;
    }

    this.selectedFile = file;
    this.message.success(`File "${file.name}" selected`);
  }

  removeFile() {
    this.selectedFile = null;
  }
  
  topic = '';
  numberOfExercises = 10;
  focus = 'grammar';
  typesOfExercises: string[] = ['multiple_choice', 'fill-in-the-blank', 'translation', 'match']; 
  
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

