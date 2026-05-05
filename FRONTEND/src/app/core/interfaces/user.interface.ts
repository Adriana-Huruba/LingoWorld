export interface User{
    id: number;
    name: string;
    email: string;
    role: "student" | "teacher" | "adult-learner";
    language: "english" | "română"| "francais" | "espanol";
    level: string | undefined;
}