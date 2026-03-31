export interface User{
    name: string;
    email: string;
    role: "student" | "teacher" | "independent";
    language: "english" | "română"| "francais" | "espanol";
    level: string | undefined;
}