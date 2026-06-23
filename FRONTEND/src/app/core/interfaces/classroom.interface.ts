export interface TeacherClassroom {
  id: number;
  name: string;
  invite_code: string;
  student_count: number;
}

export interface StudentClassroom {
  id: number;
  name: string;
  invite_code: string;
  teacher_name: string;
}

export interface ClassroomStudent {
  id: number;
  name: string;
  email: string;
  elo_score: number;
  xp: number;
}

export interface StudentProgress {
  id: number;
  name: string;
  email: string;
  exercises_attempted: number;
  exercises_correct: number;
  elo_current: number;
  xp: number;
  assignments_done: number;
}

export interface Worksheet {
  id: number;
  title: string;
  due_date: string | null;
  status: 'pending' | 'completed';
  questions: any[];
}
