export interface Exercise {
    id: number;
    type: "translation" | "multiple-choice" | "fill-in-the-blank" | "matching" | "pronunciation";
    question: string;
    options?: string[]; // only for multiple choice
    answer: string;
    level: "A1" | "A2" | "B1" | "B2" | "C1";
}
