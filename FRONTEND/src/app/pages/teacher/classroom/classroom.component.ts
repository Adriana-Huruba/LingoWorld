import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router} from '@angular/router';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzTabsModule } from 'ng-zorro-antd/tabs'; 
import { NzButtonModule } from 'ng-zorro-antd/button'; 
import { CommonModule } from '@angular/common';
import { NzSelectModule } from 'ng-zorro-antd/select';
import { FormsModule } from '@angular/forms';
import { NzInputNumberModule } from 'ng-zorro-antd/input-number';
import { NzMessageService } from 'ng-zorro-antd/message';

import { ClassroomService } from '../../../core/services/classroom.service';
import { TeacherService } from '../../../core/services/teacher.service'; 
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-classroom',
  standalone: true, 
  imports: [CommonModule, NzIconModule, NzTabsModule, NzButtonModule, FormsModule, NzSelectModule, NzInputNumberModule],
  templateUrl: './classroom.component.html',
  styleUrl: './classroom.component.scss'
})

export class ClassroomComponent implements OnInit {
  private authService = inject(AuthService);
  private classroomService = inject(ClassroomService);
  private teacherService = inject(TeacherService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private message = inject(NzMessageService);

  teacherId!: number;
  classroomID!: number;
  students: any[] = [];
  studentProgress: Map<number, { exercises_attempted: number; exercises_correct: number; elo_current: number | null; xp: number | null; assignments_done: number; }> = new Map();
  classroomName = '';
  inviteCode = '';
  errorMessage = '';
  activeTab: string = 'students';
  assignments: any[] = [];

  existingManuals: any[] = [];
  selectedFile: File | null = null;
  manualId: number | null = null;
  isDragging = false;
  isUploaded = false;

  topics: string[] = [];  // multiple topics — joined before sending to backend
  // numberOfExercises = 10;
  focus = 'grammar';
  typesOfExercises: string[] = ['multiple-choice', 'translation']; 
  exerciseCounts: { [key: string]: number } = {
    'multiple-choice': 2,
    'translation': 3
  };
  
  isGenerating = false;
  isGenerated = false;  

  worksheetTitle: string = '';
  dueDate: string = '';
  previewItems: any[] = [];
  generationConfig: any = {};

  availableExerciseTypes = [
    { value: 'multiple-choice', label: 'Multiple choice' },
    { value: 'fill-in-the-blank', label: 'Fill in the blanks' },
    { value: 'translation', label: 'Translation' },
    // { value: 'true_false', label: 'True / False' },
    { value: 'matching', label: 'Matching pairs' }
  ];
viewAssignment: any;

  ngOnInit() {
    this.teacherId = this.authService.currentUserId();

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

    this.classroomID = classroomId;
    this.loadClassroom(classroomId);
    this.loadStudents(classroomId);
    this.loadStudentProgress(classroomId);
    this.loadExistingManuals();
    this.loadAssignments(classroomId);
  }

  returnToDashboard() {
    this.router.navigate(['/homepage']);
  }

  copyInviteCode() {
    if (!this.inviteCode) 
      return;

    navigator.clipboard.writeText(this.inviteCode).then(() => {
        this.message.success(`Invite code ${this.inviteCode} copied to clipboard!`); }).catch(err => {
        this.message.error('Failed to copy code.');
        console.error('Could not copy text: ', err);
    });
  }

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }

  loadClassroom(classroomId: number) {
    this.classroomService.getClassroomById(classroomId).subscribe({
      next: (data) => {
        this.classroomName = data.name || '';
        this.inviteCode = data.invite_code || '';
      },
      error: (err) => {
        console.error('Error loading classroom details', err);
        this.errorMessage = 'Could not load classroom details.';
      }
    });
  }

  loadStudents(classroomId: number) {
    this.classroomService.getClassroomStudents(classroomId).subscribe({
      next: (data) => { this.students = data.students; },
      error: (err) => { console.error('Error loading classroom students', err); }
    });
  }

  loadStudentProgress(classroomId: number) {
    this.classroomService.getStudentProgress(classroomId).subscribe({
      next: (data) => {
        const map = new Map<number, any>();
        (data.students).forEach((s) => map.set(s.id, s));
        this.studentProgress = map;
      },
      error: (err) => { console.error('Error loading student progress', err); }
    });
  }

  loadAssignments(classroomId: number) {
    this.classroomService.getClassroomAssignments(classroomId).subscribe({
      next: (data) => {
        this.assignments = data.assignments;
      },
      error: (err) => console.error('Error loading teacher assignments', err)
    });
  }

  getProgressFor(studentId: number) {
    return this.studentProgress.get(studentId) ?? {
      exercises_attempted: 0, exercises_correct: 0,
      elo_current: null, xp: null,
      assignments_done: 0, worksheets_completed: 0, avg_score_pct: null,
    };
  }

  loadExistingManuals() {
    this.teacherService.getTeacherManuals(this.teacherId).subscribe({
      next: (data) => {
        this.existingManuals = data;
      },
      error: (err) => console.error('Error loading existing manuals', err)
    });
  }

  onExistingManualSelected(selectedManualId: number) {
    if (selectedManualId) {
      this.manualId = selectedManualId;
      this.isUploaded = true;
      this.selectedFile = null; 
      this.message.success('Existing texbook selected');
    }
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

    // const maxSizeInMB = 15; //limit 
    // if (file.size > maxSizeInMB * 1024 * 1024) {
    //   this.message.warning(`The uploaded file is too big, the limit is ${maxSizeInMB}MB!`);
    //   return;
    // }

    this.selectedFile = file;
    this.message.success(`File "${file.name}" selected`);
  }

  removeFile() {
    this.selectedFile = null;
  }

  uploadManualToAI() {
    if (!this.selectedFile) return;

    this.teacherService.uploadManual(this.selectedFile, this.teacherId, this.selectedFile.name, this.authService.targetLanguageFull, this.authService.userLevel)
      .subscribe({
        next: (res: any) => {
          this.manualId = res.manual_id;
          this.isUploaded = true;
          this.message.success('The textbook was processed by AI');
          this.loadExistingManuals();
        },
        error: (err: any) => this.message.error(err.error?.detail || 'Error at processing the textbook.')
      });
  }
  
  generateResource() {
    if (!this.topics.length || !this.manualId) {
      this.message.warning('Please add at least one topic and process the textbook first.');
      return;
    }
    
    if (this.typesOfExercises.length === 0) {
      this.message.warning('Please select at least one type of exercise.');
      return;
    }

    this.isGenerating = true;

    const counts: any = {};
    // const typesCount = this.typesOfExercises.length || 1;
    // const perType = Math.floor(this.numberOfExercises / typesCount);
    
    this.typesOfExercises.forEach(type => {
      let backendType = type;
      if (type === 'matching') 
        backendType = 'match';
 
      counts[backendType] = this.exerciseCounts[type];
    });

    const payload = {
      teacher_id: this.teacherId,
      manual_id: this.manualId,
      exercise_counts: counts,
      level: this.authService.userLevel,
      language: this.authService.targetLanguageFull,
      topic: this.topics.join(', '),
      native_language: this.authService.nativeLanguageFull,
      extra_instructions: `Special focus on: ${this.focus}`
    };

    this.teacherService.previewWorksheet(payload).subscribe({
      next: (res: any) => {
        this.previewItems = res.items;
        this.generationConfig = res.generation_config;
        this.isGenerating = false;
        this.isGenerated = true;

        if (res.items.length === 0) {
          this.message.error(`Generation failed: 0/${res.total_requested} exercises created`);
        } else if (res.total_failed > 0) {
          this.message.warning(`Generated ${res.total_generated}/${res.total_requested} exercises`);
        } else {
          this.message.success('The assistant generated the exercises');
        }
      },
      error: (err: any) => {
        this.message.error(err.error?.detail || 'Generation failed..');
        this.isGenerating = false;
      }
    });
  }

  onExerciseTypesChange(selectedTypes: string[]) {
    selectedTypes.forEach(type => {
      if (!this.exerciseCounts[type]) {
        this.exerciseCounts[type] = 2; 
      }
    });
  }

  getLabelForType(value: string): string {
    const found = this.availableExerciseTypes.find(t => t.value === value);
    return found ? found.label : value;
  }

  removeItem(index: number) {
    this.previewItems.splice(index, 1);
  }

  get totalExercisesCount(): number {
    let total = 0;
    for (const type of this.typesOfExercises) {
      if (this.exerciseCounts[type]) {
        total += this.exerciseCounts[type];
      }
    }
    return total;
  }

  regenerateItem(index: number) {
    const itemToRegen = this.previewItems[index];
    const payload = {
      teacher_id: this.teacherId,
      exercise_type: itemToRegen.exercise_type,
      generation_config: this.generationConfig
    };

    this.teacherService.regenerateItem(payload).subscribe({
      next: (newItem: any) => {
        this.previewItems[index] = newItem;
        this.message.success('The exercise was regenerated');
      },
      error: () => this.message.error('Regeneration failed..')
    });
  }

  publishWorksheet() {
    if (!this.worksheetTitle || this.previewItems.length === 0) {
      this.message.warning('Insert a title for the assignment');
      return;
    }

    const payload = {
      teacher_id: this.teacherId,
      manual_id: this.manualId,
      classroom_id: this.classroomID,
      title: this.worksheetTitle,
      due_date: this.dueDate ? new Date(this.dueDate).toISOString() : null,
      items: this.previewItems.map(item => ({
        exercise_type: item.exercise_type,
        content: item.content,
        correct_answer: item.correct_answer,
        elo_difficulty: item.elo_difficulty
      })),
      config: { topic: this.topics.join(', ') }
    };

    this.teacherService.publishWorksheet(payload).subscribe({
      next: (res: any) => {
        this.message.success(`The worksheet was sent to the class`);
        this.previewItems = [];
        this.isGenerated = false;
        this.worksheetTitle = '';
        this.loadAssignments(this.classroomID);
        this.setActiveTab('assignments'); 
      },
      error: () => this.message.error('Error at publication.')
    });
  }
}

