from typing import Literal

from pydantic import BaseModel, Field, model_validator


QuestionType = Literal[
    "Multiple Choice",
    "True or False",
    "Fill in the Blanks",
    "Short Answer",
    "Essay",
    "Problem Solving",
]
Difficulty = Literal["Easy", "Medium", "Hard"]


class GenerateRequest(BaseModel):
    lesson_id: str
    title: str = Field(min_length=1, max_length=160)
    grade: int = Field(ge=5, le=12)
    subject: str = Field(min_length=1, max_length=100)
    total_marks: int = Field(ge=1, le=1000)
    duration_minutes: int = Field(ge=1, le=600)
    question_count: int = Field(ge=1, le=100)
    difficulty: Literal["Easy", "Medium", "Hard", "Mixed"]
    question_types: list[QuestionType] = Field(min_length=1)
    language: Literal["Khmer", "English"] = "Khmer"

    @model_validator(mode="after")
    def validate_mark_capacity(self):
        if self.total_marks < self.question_count:
            raise ValueError("Total marks must be at least the number of questions.")
        return self


class Question(BaseModel):
    type: QuestionType
    text: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)
    answer: str = Field(min_length=1)
    explanation: str = ""
    rubric: str = ""
    marks: int = Field(ge=1)
    difficulty: Difficulty = "Medium"


class ExamData(BaseModel):
    title: str = Field(min_length=1)
    grade: int = Field(ge=5, le=12)
    subject: str = Field(min_length=1)
    total_marks: int = Field(ge=1)
    duration_minutes: int = Field(ge=1)
    language: Literal["Khmer", "English"] = "Khmer"
    questions: list[Question] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_marks(self):
        if sum(question.marks for question in self.questions) != self.total_marks:
            raise ValueError("Question marks must add up to the total exam marks.")
        return self


class ExamUpdate(ExamData):
    pass


class RegenerateQuestionRequest(BaseModel):
    lesson_id: str
    grade: int = Field(ge=5, le=12)
    subject: str = Field(min_length=1, max_length=100)
    question_type: QuestionType
    difficulty: Difficulty
    language: Literal["Khmer", "English"] = "Khmer"
    marks: int = Field(ge=1)
    existing_questions: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    lesson_id: str | None = None
    language: Literal["Khmer", "English"] = "Khmer"
