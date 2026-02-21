export class User{
    name!: string;
    email!: string;
    role: "student" | "teacher" | "independent" = "student";
    language: "english" | "română"| "francais" | "espanol" = "english";
    level: string | undefined;
}