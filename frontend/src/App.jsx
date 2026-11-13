import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownToLine, ArrowLeft, ArrowRight, BookOpen, Check, CheckCircle2, ChevronDown,
  ClipboardList, Clock3, FileText, GraduationCap, LayoutDashboard, LoaderCircle, LogOut, Menu,
  MessageCircle, Plus, RefreshCw, Sparkles, Trash2, Upload, X,
} from "lucide-react";
import { useAuth } from "./AuthContext";
import AuthForm from "./AuthForm";
import { apiFetch as api } from "./utils/apiFetch";

const questionTypes = ["Multiple Choice", "True or False", "Fill in the Blanks", "Short Answer", "Essay", "Problem Solving"];
const subjects = ["Khmer Literature", "Mathematics", "Phycs", "Chemistry", "Biology", "History", "Geography", "English", "Other"];
const initialForm = {
  title: "Mid-term Examination", grade: "9", subject: "Mathematics", total_marks: "50",
  duration_minutes: "90", question_count: "10", difficulty: "Mixed",
  question_types: ["Multiple Choice", "Short Answer", "Problem Solving"], language: "Khmer",
};
const copy = {
  en: {
    nav: ["Dashboard", "Upload lesson", "Generate exam", "Chat with AI"],
    greeting: "Good morning, Teacher", welcome: "Your classroom, made easier.",
    intro: "Turn your teaching materials into thoughtful, curriculum-aligned assessments in minutes.",
    create: "Create an examination", lessons: "Lesson library", recent: "Recent examinations",
    upload: "Upload lesson", uploadHint: "PDF, DOCX, PPTX or TXT · Up to 20 MB",
    generate: "Generate examination", generateHint: "Configure a paper using your lesson material.",
    preview: "Examination preview", paper: "Student paper", answerKey: "Answer key",
    download: "Download", save: "Save changes", regenerate: "Regenerate", addQuestion: "Add question",
    subject: "Subject", grade: "Grade", title: "Examination title", marks: "Total marks",
    duration: "Duration (minutes)", count: "Number of questions", difficulty: "Difficulty",
    types: "Question types", language: "Output language", chooseLesson: "Choose lesson material",
    generateBtn: "Generate examination", generating: "Creating your examination...",
    chat: "ExamGen assistant", chatIntro: "I’ll guide you through preparing a paper from your lesson.",
    chatPlaceholder: "Ask about your exam...", send: "Send", total: "Total", questions: "Questions",
    minutes: "minutes", noLessons: "No lesson materials yet", noExams: "No examinations yet",
    start: "Start by uploading a lesson", delete: "Delete", deleteConfirm: "Delete this examination? This cannot be undone.",
    deleted: "Examination deleted.", deleteLessonConfirm: "Delete this uploaded lesson? Exams made from it will remain, but lesson-based regeneration will no longer work.",
    lessonDeleted: "Uploaded lesson deleted.", edit: "Edit question",
    remove: "Remove question", subjectOther: "Enter subject", answer: "Answer (teacher only)",
    explanation: "Explanation", rubric: "Grading criteria", options: "Answer choices",
    original: "Grounded in your uploaded lesson", emptyChat: "Upload a lesson and tell me your grade and subject to get started.",
  },
  km: {
    nav: ["ផ្ទាំងគ្រប់គ្រង", "បញ្ចូលមេរៀន", "បង្កើតវិញ្ញាសា", "ជជែកជាមួយ AI"],
    greeting: "អរុណសួស្តី លោកគ្រូ/អ្នកគ្រូ", welcome: "ការបង្រៀនកាន់តែងាយស្រួល។",
    intro: "បង្កើតវិញ្ញាសាពីឯកសារមេរៀនរបស់លោកគ្រូ/អ្នកគ្រូ ក្នុងរយៈពេលតែប៉ុន្មាននាទី។",
    create: "បង្កើតវិញ្ញាសា", lessons: "បណ្ណាល័យមេរៀន", recent: "វិញ្ញាសាថ្មីៗ",
    upload: "បញ្ចូលមេរៀន", uploadHint: "PDF, DOCX, PPTX ឬ TXT · ទំហំមិនលើស ២០ MB",
    generate: "បង្កើតវិញ្ញាសា", generateHint: "កំណត់វិញ្ញាសាដោយប្រើឯកសារមេរៀនរបស់អ្នក។",
    preview: "ពិនិត្យវិញ្ញាសា", paper: "វិញ្ញាសាសិស្ស", answerKey: "គន្លឹះចម្លើយ",
    download: "ទាញយក", save: "រក្សាទុក", regenerate: "បង្កើតឡើងវិញ", addQuestion: "បន្ថែមសំណួរ",
    subject: "មុខវិជ្ជា", grade: "ថ្នាក់ទី", title: "ចំណងជើងវិញ្ញាសា", marks: "ពិន្ទុសរុប",
    duration: "រយៈពេល (នាទី)", count: "ចំនួនសំណួរ", difficulty: "កម្រិតពិបាក",
    types: "ប្រភេទសំណួរ", language: "ភាសា", chooseLesson: "ជ្រើសរើសមេរៀន",
    generateBtn: "បង្កើតវិញ្ញាសា", generating: "កំពុងបង្កើតវិញ្ញាសា...",
    chat: "ជំនួយការ ExamGen", chatIntro: "ខ្ញុំនឹងជួយរៀបចំវិញ្ញាសាពីមេរៀនរបស់អ្នក។",
    chatPlaceholder: "សួរអំពីវិញ្ញាសារបស់អ្នក...", send: "ផ្ញើ", total: "សរុប", questions: "សំណួរ",
    minutes: "នាទី", noLessons: "មិនទាន់មានមេរៀនទេ", noExams: "មិនទាន់មានវិញ្ញាសាទេ",
    start: "ចាប់ផ្ដើមដោយបញ្ចូលមេរៀន", delete: "លុប",
    deleteConfirm: "តើអ្នកប្រាកដថាចង់លុបវិញ្ញាសានេះទេ? ការលុបនេះមិនអាចត្រឡប់វិញបានទេ។",
    deleted: "បានលុបវិញ្ញាសា។",
    deleteLessonConfirm: "តើអ្នកប្រាកដថាចង់លុបមេរៀនដែលបានបញ្ចូលនេះទេ? វិញ្ញាសាដែលបានបង្កើតនឹងនៅដដែល ប៉ុន្តែមិនអាចបង្កើតសំណួរឡើងវិញដោយប្រើមេរៀននេះបានទេ។",
    lessonDeleted: "បានលុបមេរៀនដែលបានបញ្ចូល។", edit: "កែសំណួរ",
    remove: "លុបសំណួរ", subjectOther: "បញ្ចូលមុខវិជ្ជា", answer: "ចម្លើយ (សម្រាប់គ្រូប៉ុណ្ណោះ)",
    explanation: "ការពន្យល់", rubric: "លក្ខណៈវិនិច្ឆ័យដាក់ពិន្ទុ", options: "ជម្រើសចម្លើយ",
    original: "ផ្អែកលើមេរៀនដែលបានបញ្ចូល", emptyChat: "បញ្ចូលមេរៀន ហើយប្រាប់ខ្ញុំពីថ្នាក់ និងមុខវិជ្ជា ដើម្បីចាប់ផ្តើម។",
  },
};

const cx = (...values) => values.filter(Boolean).join(" ");

function App() {
  const {
    user,
    session: authSession,
    loading: authLoading,
    error: authError,
    signOut: authSignOut,
    authNotice,
    setAuthNotice,
  } = useAuth();
  const [language, setLanguage] = useState("en");
  const t = copy[language];
  const [page, setPage] = useState("Dashboard");
  const [lessons, setLessons] = useState([]);
  const [exams, setExams] = useState([]);
  const [lessonId, setLessonId] = useState("");
  const [exam, setExam] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [mobileMenu, setMobileMenu] = useState(false);
  const [activeTab, setActiveTab] = useState("paper");
  const [editing, setEditing] = useState(-1);
  const [customSubject, setCustomSubject] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatText, setChatText] = useState("");
  const chatInFlight = useRef(false);
  const fileInput = useRef(null);
  const chatEnd = useRef(null);
  const isKhmer = language === "km";
  const sumMarks = useMemo(() => exam?.questions?.reduce((sum, q) => sum + Number(q.marks || 0), 0) || 0, [exam]);

  useEffect(() => {
    if (!authNotice) return;
    setNotice(authNotice);
    setAuthNotice("");
  }, [authNotice, setAuthNotice]);

  async function refresh() {
    try {
      const [lessonResponse, examResponse] = await Promise.all([api("/api/lessons"), api("/api/exams")]);
      const availableLessons = await lessonResponse.json();
      setLessons(availableLessons);
      setLessonId((current) => availableLessons.some((lesson) => lesson.id === current)
        ? current
        : availableLessons[0]?.id || "");
      setExams(await examResponse.json());
    } catch (e) { setError(e.message); }
  }
  useEffect(() => {
    if (authSession) {
      refresh();
    } else if (!authLoading) {
      setLessons([]);
      setExams([]);
      setExam(null);
    }
  }, [authLoading, authSession]);
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [chatMessages]);

  async function signOut() {
    try {
      await authSignOut();
      setError("");
    } catch (signOutError) {
      setError(signOutError.message);
    }
  }

  function navigate(nextPage) {
    setPage(nextPage);
    setError("");
    setMobileMenu(false);
    if (nextPage === "Chat with AI" && !chatMessages.length) {
      setChatMessages([{ role: "assistant", text: t.chatIntro + " " + t.emptyChat }]);
    }
  }
  async function uploadFile(file) {
    if (!file) return;
    setBusy("upload"); setError(""); setNotice("");
    const data = new FormData(); data.append("file", file);
    try {
      const response = await api("/api/lessons", { method: "POST", body: data });
      const result = await response.json();
      await refresh(); setLessonId(result.id); setNotice(`"${result.filename}" uploaded — ${result.character_count.toLocaleString()} characters extracted.`);
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  function updateForm(key, value) { setForm((current) => ({ ...current, [key]: value })); }
  async function generate() {
    const subject = form.subject === "Other" ? customSubject.trim() : form.subject;
    if (!lessonId) { setError("Upload or select a lesson before generating an examination."); return; }
    if (!subject) { setError("Please enter a subject."); return; }
    setBusy("generate"); setError(""); setNotice("");
    try {
      const response = await api("/api/exams/generate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, grade: Number(form.grade), subject, total_marks: Number(form.total_marks),
          duration_minutes: Number(form.duration_minutes), question_count: Number(form.question_count) }),
      });
      const result = await response.json(); setExam(result); setActiveTab("paper"); setEditing(-1); setPage("Examination Preview"); await refresh();
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  async function saveExam(updated = exam) {
    if (!updated) return;
    const total = updated.questions.reduce((sum, question) => sum + Number(question.marks || 0), 0);
    if (total !== Number(updated.total_marks)) { setError(`Question marks total ${total}; the examination is set to ${updated.total_marks}.`); return false; }
    setBusy("save"); setError("");
    try {
      const response = await api(`/api/exams/${updated.id}`, { method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.fromEntries(["title", "grade", "subject", "total_marks", "duration_minutes", "language", "questions"].map((key) => [key, updated[key]]))) });
      setExam(await response.json()); setNotice("Changes saved."); await refresh(); return true;
    } catch (e) { setError(e.message); return false; }
    finally { setBusy(""); }
  }
  async function deleteExam(item) {
    if (!window.confirm(`${t.deleteConfirm}\n\n${item.title}`)) return;
    setBusy(`delete-${item.id}`); setError(""); setNotice("");
    try {
      await api(`/api/exams/${item.id}`, { method: "DELETE" });
      setExams((current) => current.filter((savedExam) => savedExam.id !== item.id));
      if (exam?.id === item.id) {
        setExam(null);
        setPage("Dashboard");
      }
      setNotice(t.deleted);
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  async function deleteLesson(item) {
    if (!window.confirm(`${t.deleteLessonConfirm}\n\n${item.filename}`)) return;
    setBusy(`delete-lesson-${item.id}`); setError(""); setNotice("");
    try {
      await api(`/api/lessons/${item.id}`, { method: "DELETE" });
      setLessons((current) => current.filter((lesson) => lesson.id !== item.id));
      if (lessonId === item.id) setLessonId(lessons.find((lesson) => lesson.id !== item.id)?.id || "");
      setNotice(t.lessonDeleted);
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  async function regenerate(index) {
    const q = exam.questions[index]; setBusy(`question-${index}`); setError("");
    try {
      const response = await api(`/api/exams/${exam.id}/questions/regenerate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lesson_id: exam.lesson_id, grade: exam.grade, subject: exam.subject,
          question_type: q.type, difficulty: q.difficulty, language: exam.language, marks: q.marks,
          existing_questions: exam.questions.filter((_, i) => i !== index).map((question) => question.text) }),
      });
      const replacement = await response.json();
      setExam((current) => ({ ...current, questions: current.questions.map((question, i) => i === index ? replacement : question) }));
      setNotice("Question regenerated. Save changes to keep it.");
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  async function regenerateKey() {
    setBusy("answer-key"); setError("");
    try {
      const response = await api(`/api/exams/${exam.id}/answer-key/regenerate`, { method: "POST" });
      setExam(await response.json()); setNotice("Answer key regenerated.");
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  async function download(documentType, format) {
    setError("");
    try {
      if (!await saveExam(exam)) return;
      setBusy(`download-${documentType}-${format}`);
      const response = await api(`/api/exams/${exam.id}/export?format=${format}&document=${documentType}`);
      const blob = await response.blob(); const url = URL.createObjectURL(blob);
      const link = document.createElement("a"); link.href = url; link.download = `${exam.title.replace(/[^\p{L}\p{N}-]+/gu, "_")}-${documentType}.${format}`;
      document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  function patchQuestion(index, key, value) {
    setExam((current) => ({ ...current, questions: current.questions.map((q, i) => i === index ? { ...q, [key]: value } : q) }));
  }
  async function sendChat(event) {
    event.preventDefault();
    const message = chatText.trim();
    if (!message || chatInFlight.current) return;
    chatInFlight.current = true;
    const updatedMessages = [...chatMessages, { role: "teacher", text: message }];
    setChatMessages(updatedMessages); setChatText(""); setBusy("chat"); setError("");
    try {
      const response = await api("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          language: isKhmer ? "Khmer" : "English",
          lesson_id: lessonId || null,
          messages: updatedMessages.slice(-12).map((item) => ({
            role: item.role === "teacher" ? "user" : "assistant",
            content: item.text,
          })),
        }),
      });
      const result = await response.json();
      setChatMessages((list) => [...list, { role: "assistant", text: result.reply }]);
    } catch (e) { setError(e.message); }
    finally { chatInFlight.current = false; setBusy(""); }
  }

  const nav = [
    { name: "Dashboard", icon: LayoutDashboard },
    { name: "Upload lesson", icon: Upload },
    { name: "Generate exam", icon: Sparkles },
    { name: "Chat with AI", icon: MessageCircle },
  ];
  const activeNav = page === "Generate examination" ? "Generate exam" : page;

  if (authLoading) {
    return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Checking your session...</div>;
  }
  if (!user) {
    return <AuthForm initialError={authError} />;
  }

  return (
    <div className={cx("min-h-screen", isKhmer && "khmer")}>
      <aside className={cx("fixed inset-y-0 left-0 z-30 flex w-[248px] flex-col border-r border-slate-100 bg-white px-5 py-6 transition-transform lg:translate-x-0 no-print", mobileMenu ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex items-center gap-3 px-1">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-200"><BookOpen size={20} /></div>
          <div><p className="text-[15px] font-extrabold tracking-tight text-ink">ExamGen <span className="text-indigo-600">AI</span></p><p className="text-[10px] font-semibold tracking-[.15em] text-slate-400">KHMER EDUCATION</p></div>
        </div>
        <div className="mt-10">
          <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.17em] text-slate-400">{isKhmer ? "ម៉ឺនុយ" : "Workspace"}</p>
          <nav className="space-y-1">
            {nav.map(({ name, icon: Icon }, index) => <button key={name} onClick={() => navigate(name === "Generate exam" ? "Generate examination" : name)} className={cx("flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[13px] font-semibold transition", activeNav === name ? "bg-indigo-50 text-indigo-700" : "text-slate-500 hover:bg-slate-50 hover:text-ink")}>
              <Icon size={17} strokeWidth={2} /><span>{t.nav[index]}</span>{name === "Chat with AI" && <span className="ml-auto rounded-full bg-emerald-100 px-2 py-0.5 text-[9px] font-bold text-emerald-700">AI</span>}
            </button>)}
          </nav>
        </div>
        <div className="mt-9">
          <div className="mb-3 flex items-center justify-between px-3"><p className="text-[10px] font-bold uppercase tracking-[.17em] text-slate-400">{isKhmer ? "ថ្មីៗ" : "Recent exams"}</p><button aria-label="Create exam" onClick={() => navigate("Generate examination")} className="rounded-md p-1 text-slate-400 hover:bg-slate-100"><Plus size={15} /></button></div>
          <div className="space-y-1">{exams.slice(0, 4).map((item) => <div key={item.id} className="flex items-center rounded-lg hover:bg-slate-50">
            <button onClick={() => { setExam(item); navigate("Examination Preview"); }} className="flex min-w-0 flex-1 items-center gap-2.5 truncate px-3 py-2 text-left text-xs text-slate-500"><FileText size={14} className="shrink-0 text-slate-400" /><span className="truncate">{item.title}</span></button>
            <button aria-label={`${t.delete} ${item.title}`} title={t.delete} disabled={busy === `delete-${item.id}`} onClick={() => deleteExam(item)} className="mr-2 rounded-md p-1 text-slate-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"><Trash2 size={13} /></button>
          </div>)}</div>
        </div>
        <div className="mt-auto rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 p-4 text-white">
          <div className="mb-3 grid h-8 w-8 place-items-center rounded-lg bg-white/15"><Sparkles size={16} /></div>
          <p className="text-xs font-bold">{isKhmer ? "បង្កើតវិញ្ញាសាឆ្លាតវៃ" : "Thoughtful exams, faster"}</p>
          <p className="mt-1 text-[10px] leading-5 text-indigo-100">{isKhmer ? "ផ្អែកលើមេរៀនរបស់អ្នក" : "Grounded in your own lesson materials."}</p>
          <button onClick={() => navigate("Generate examination")} className="mt-3 flex items-center gap-1 text-[10px] font-bold">{isKhmer ? "ចាប់ផ្តើម" : "Create an exam"} <ArrowRight size={12} /></button>
        </div>
        <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-4">
          <div className="grid h-9 w-9 place-items-center rounded-full bg-amber-100 text-sm font-bold text-amber-700">T</div>
          <div className="min-w-0"><p className="truncate text-xs font-bold text-ink">{user.email}</p><p className="text-[10px] text-slate-400">Educator workspace</p></div>
          <button onClick={() => setLanguage(isKhmer ? "en" : "km")} className="ml-auto rounded-lg border border-slate-200 px-2 py-1 text-[10px] font-bold text-slate-500">{isKhmer ? "EN" : "ខ្មែរ"}</button>
          <button aria-label="Sign out" title="Sign out" onClick={signOut} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-rose-600"><LogOut size={15} /></button>
        </div>
      </aside>
      {mobileMenu && <button aria-label="Close menu" onClick={() => setMobileMenu(false)} className="fixed inset-0 z-20 bg-slate-900/20 lg:hidden no-print" />}
      <main className="min-h-screen lg:ml-[248px]">
        <header className="sticky top-0 z-10 flex h-[68px] items-center justify-between border-b border-slate-100 bg-white/90 px-5 backdrop-blur md:px-9 no-print">
          <div className="flex items-center gap-3"><button onClick={() => setMobileMenu(true)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"><Menu size={19} /></button>
            <div className="hidden items-center gap-2 text-xs text-slate-400 sm:flex"><span>Workspace</span><span>/</span><span className="font-semibold text-slate-700">{page}</span></div>
            <h1 className="text-sm font-bold text-ink sm:hidden">{page === "Dashboard" ? "ExamGen AI" : page}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-[10px] font-semibold text-emerald-700 sm:flex"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />{isKhmer ? "ប្រព័ន្ធដំណើរការ" : "AI workspace ready"}</span>
            <button onClick={() => setLanguage(isKhmer ? "en" : "km")} className="rounded-lg border border-slate-200 px-2.5 py-1.5 text-[11px] font-bold text-slate-500 lg:hidden">{isKhmer ? "EN" : "ខ្មែរ"}</button>
            <div className="grid h-8 w-8 place-items-center rounded-full bg-amber-100 text-xs font-bold text-amber-700">T</div>
          </div>
        </header>
        <div className="mx-auto max-w-[1320px] px-5 py-7 md:px-9 md:py-9">
          {error && <div role="alert" className="mb-5 flex items-start gap-2 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-xs leading-5 text-rose-700"><X size={15} className="mt-0.5 shrink-0" />{error}<button onClick={() => setError("")} className="ml-auto"><X size={15} /></button></div>}
          {notice && <div role="status" className="mb-5 flex items-center gap-2 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-xs text-emerald-700"><CheckCircle2 size={15} />{notice}<button onClick={() => setNotice("")} className="ml-auto"><X size={15} /></button></div>}
          {page === "Dashboard" && <Dashboard t={t} lessons={lessons} exams={exams} busy={busy} onNavigate={navigate} onDeleteExam={deleteExam} onDeleteLesson={deleteLesson} onOpenExam={(item) => { setExam(item); navigate("Examination Preview"); }} />}
          {page === "Upload lesson" && <UploadPage t={t} lessons={lessons} busy={busy} onFile={uploadFile} onDeleteLesson={deleteLesson} inputRef={fileInput} />}
          {page === "Generate examination" && <GeneratePage t={t} lessons={lessons} form={form} onChange={updateForm} lessonId={lessonId} setLessonId={setLessonId} customSubject={customSubject} setCustomSubject={setCustomSubject} busy={busy} onGenerate={generate} onUpload={() => fileInput.current?.click()} />}
          {page === "Examination Preview" && exam && <PreviewPage t={t} exam={exam} activeTab={activeTab} setActiveTab={setActiveTab} editing={editing} setEditing={setEditing} busy={busy} sumMarks={sumMarks} onPatch={patchQuestion} onSave={saveExam} onRegenerate={regenerate} onRegenerateKey={regenerateKey} onDownload={download} onAdd={() => { setExam((current) => ({ ...current, questions: [...current.questions, { type: "Short Answer", text: "", options: [], answer: "", explanation: "", rubric: "", marks: 1, difficulty: "Medium" }], total_marks: Number(current.total_marks) + 1 })); setEditing(exam.questions.length); }} onRemove={(index) => { const questions = exam.questions.filter((_, i) => i !== index); const removed = exam.questions[index].marks; setExam({ ...exam, questions, total_marks: Math.max(questions.length, exam.total_marks - removed) }); }} />}
          {page === "Examination Preview" && !exam && <EmptyPanel t={t} onAction={() => navigate("Generate examination")} />}
          {page === "Chat with AI" && <ChatPage t={t} messages={chatMessages} value={chatText} setValue={setChatText} onSend={sendChat} endRef={chatEnd} busy={busy === "chat"} onGenerate={() => navigate("Generate examination")} />}
          <input ref={fileInput} type="file" accept=".pdf,.docx,.pptx,.txt" className="hidden" onChange={(event) => { uploadFile(event.target.files?.[0]); event.target.value = ""; }} />
        </div>
      </main>
    </div>
  );
}

function SectionTitle({ eyebrow, title, description, action }) {
  return <div className="mb-7 flex flex-wrap items-end justify-between gap-4"><div>{eyebrow && <p className="mb-2 text-[10px] font-bold uppercase tracking-[.18em] text-indigo-600">{eyebrow}</p>}<h2 className="text-2xl font-extrabold tracking-tight text-ink">{title}</h2>{description && <p className="mt-2 text-sm text-slate-500">{description}</p>}</div>{action}</div>;
}
function Button({ children, onClick, variant = "primary", disabled, icon: Icon, className = "" }) {
  const variants = { primary: "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm shadow-indigo-200", secondary: "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50", ghost: "text-slate-500 hover:bg-slate-100", danger: "text-rose-600 hover:bg-rose-50" };
  return <button disabled={disabled} onClick={onClick} className={cx("inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-55", variants[variant], className)}>{Icon && <Icon size={15} />}{children}</button>;
}
function Dashboard({ t, lessons, exams, busy, onNavigate, onDeleteExam, onDeleteLesson, onOpenExam }) {
  return <div className="animate-in">
    <div className="relative mb-8 overflow-hidden rounded-[24px] bg-gradient-to-r from-[#1a2450] via-[#393c85] to-[#675ce4] p-7 text-white md:p-10">
      <div className="relative z-[1] max-w-[590px]"><div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-[10px] font-semibold text-indigo-100"><Sparkles size={13} /> AI-POWERED ASSESSMENT STUDIO</div>
        <h2 className={cx("text-2xl font-extrabold leading-tight tracking-tight md:text-[32px]", t === copy.km && "khmer")}>{t.welcome}</h2><p className="mt-3 max-w-lg text-sm leading-6 text-indigo-100">{t.intro}</p>
        <Button onClick={() => onNavigate("Generate examination")} className="mt-6 bg-white !text-indigo-700 shadow-none hover:bg-indigo-50" icon={Plus}>{t.create}</Button>
      </div>
      <div className="pointer-events-none absolute -right-7 -top-20 h-72 w-72 rounded-full border border-white/10" /><div className="pointer-events-none absolute -right-0 -top-12 h-56 w-56 rounded-full border border-white/10" />
      <div className="pointer-events-none absolute bottom-0 right-[12%] hidden opacity-20 md:block"><GraduationCap size={136} strokeWidth={0.8} /></div>
    </div>
    <div className="mb-8 grid gap-4 sm:grid-cols-3">
      <StatCard icon={BookOpen} label={t.lessons} value={lessons.length} tone="indigo" />
      <StatCard icon={ClipboardList} label={t.recent} value={exams.length} tone="violet" />
      <StatCard icon={GraduationCap} label={t.grade} value="5–12" tone="amber" />
    </div>
    <div className="grid gap-6 xl:grid-cols-[1.4fr_.8fr]">
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-card md:p-6">
        <div className="mb-5 flex items-center justify-between"><div><h3 className="text-sm font-bold text-ink">{t.recent}</h3><p className="mt-1 text-[11px] text-slate-400">Review, edit, or export your papers</p></div><button onClick={() => onNavigate("Generate examination")} className="rounded-lg p-2 text-indigo-600 hover:bg-indigo-50"><Plus size={17} /></button></div>
        {exams.length ? <div className="divide-y divide-slate-100">{exams.slice(0, 5).map((item) => <div key={item.id} className="flex items-center gap-2 py-3">
          <button onClick={() => onOpenExam(item)} className="flex min-w-0 flex-1 items-center gap-3 text-left hover:bg-slate-50/70">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><FileText size={16} /></div><div className="min-w-0 flex-1"><p className="truncate text-xs font-bold text-ink">{item.title}</p><p className="mt-1 text-[10px] text-slate-400">Grade {item.grade} · {item.subject} · {item.total_marks} marks</p></div><ArrowRight size={15} className="text-slate-300" />
          </button>
          <button aria-label={`${t.delete} ${item.title}`} title={t.delete} disabled={busy === `delete-${item.id}`} onClick={() => onDeleteExam(item)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"><Trash2 size={15} /></button>
        </div>)}</div> : <EmptyState text={t.noExams} cta={t.create} onClick={() => onNavigate("Generate examination")} />}
      </div>
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-card md:p-6"><div className="mb-5 flex items-center justify-between"><div><h3 className="text-sm font-bold text-ink">{t.lessons}</h3><p className="mt-1 text-[11px] text-slate-400">{lessons.length} source {lessons.length === 1 ? "document" : "documents"}</p></div><button onClick={() => onNavigate("Upload lesson")} className="rounded-lg p-2 text-indigo-600 hover:bg-indigo-50"><Upload size={16} /></button></div>
        {lessons.length ? <div className="space-y-3">{lessons.slice(0, 4).map((lesson) => <div key={lesson.id} className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-50 text-emerald-600"><FileText size={16} /></div><div className="min-w-0 flex-1"><p className="truncate text-xs font-bold text-ink">{lesson.filename}</p><p className="text-[10px] text-slate-400">{(lesson.character_count || 0).toLocaleString()} characters</p></div><button aria-label={`${t.delete} ${lesson.filename}`} title={t.delete} disabled={busy === `delete-lesson-${lesson.id}`} onClick={() => onDeleteLesson(lesson)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"><Trash2 size={14} /></button></div>)}</div> : <EmptyState text={t.noLessons} cta={t.upload} onClick={() => onNavigate("Upload lesson")} />}
      </div>
    </div>
  </div>;
}
function StatCard({ icon: Icon, label, value, tone }) {
  const colors = { indigo: "bg-indigo-50 text-indigo-600", violet: "bg-violet-50 text-violet-600", amber: "bg-amber-50 text-amber-600" };
  return <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-card"><div className="flex items-center justify-between"><span className="text-[11px] font-semibold text-slate-500">{label}</span><span className={cx("grid h-9 w-9 place-items-center rounded-xl", colors[tone])}><Icon size={17} /></span></div><p className="mt-3 text-2xl font-extrabold text-ink">{value}</p></div>;
}
function EmptyState({ text, cta, onClick }) {
  return <div className="flex flex-col items-center py-9 text-center"><div className="mb-3 grid h-11 w-11 place-items-center rounded-2xl bg-slate-50 text-slate-400"><FileText size={19} /></div><p className="text-xs text-slate-500">{text}</p><button onClick={onClick} className="mt-3 text-[11px] font-bold text-indigo-600">{cta}</button></div>;
}
function EmptyPanel({ t, onAction }) { return <div className="rounded-2xl border border-slate-100 bg-white p-8 shadow-card"><EmptyState text={t.noExams} cta={t.generateBtn} onClick={onAction} /></div>; }

function UploadPage({ t, lessons, busy, onFile, onDeleteLesson, inputRef }) {
  const [drag, setDrag] = useState(false);
  return <div><SectionTitle eyebrow="SOURCE MATERIALS" title={t.upload} description="Upload teaching materials to ground your AI-generated questions in your lesson." />
    <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={(e) => { e.preventDefault(); setDrag(false); onFile(e.dataTransfer.files?.[0]); }}
      onClick={() => inputRef.current?.click()} className={cx("cursor-pointer rounded-[22px] border-2 border-dashed bg-white px-6 py-14 text-center shadow-card transition", drag ? "border-indigo-400 bg-indigo-50/50" : "border-slate-200 hover:border-indigo-300")}>
      <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-indigo-50 text-indigo-600">{busy === "upload" ? <LoaderCircle size={23} className="animate-spin" /> : <Upload size={23} />}</div>
      <p className="text-sm font-bold text-ink">{busy === "upload" ? "Extracting lesson text..." : "Choose a lesson file or drag it here"}</p>
      <p className="mt-2 text-xs text-slate-400">{t.uploadHint}</p>
      <Button className="mt-5" icon={Upload} disabled={busy === "upload"}>Browse files</Button>
    </div>
    <div className="mt-7 rounded-2xl border border-slate-100 bg-white p-5 shadow-card md:p-6"><h3 className="mb-4 text-sm font-bold text-ink">{t.lessons}<span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-500">{lessons.length}</span></h3>
      {lessons.length ? <div className="divide-y divide-slate-100">{lessons.map((lesson) => <div key={lesson.id} className="flex items-center gap-3 py-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-emerald-600"><FileText size={17} /></div><div className="min-w-0 flex-1"><p className="truncate text-xs font-bold text-ink">{lesson.filename}</p><p className="mt-1 text-[10px] text-slate-400">{(lesson.character_count || 0).toLocaleString()} characters extracted</p></div><button aria-label={`${t.delete} ${lesson.filename}`} title={t.delete} disabled={busy === `delete-lesson-${lesson.id}`} onClick={() => onDeleteLesson(lesson)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"><Trash2 size={15} /></button></div>)}</div> : <EmptyState text={t.noLessons} cta="Upload your first lesson" onClick={() => inputRef.current?.click()} />}
    </div>
  </div>;
}

function GeneratePage({ t, lessons, form, onChange, lessonId, setLessonId, customSubject, setCustomSubject, busy, onGenerate, onUpload }) {
  const toggleType = (type) => onChange("question_types", form.question_types.includes(type) ? form.question_types.filter((item) => item !== type) : [...form.question_types, type]);
  const selectedLesson = lessons.find((lesson) => lesson.id === lessonId);
  return <div><SectionTitle eyebrow="EXAM BUILDER" title={t.generate} description={t.generateHint} />
    <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
      <div className="space-y-5">
        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-card md:p-7">
          <div className="mb-5 flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><ClipboardList size={17} /></span><div><h3 className="text-sm font-bold text-ink">Exam details</h3><p className="text-[10px] text-slate-400">Set the class and assessment format</p></div></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t.title} className="sm:col-span-2"><input value={form.title} onChange={(e) => onChange("title", e.target.value)} className="input" placeholder="e.g. Mid-term Examination" /></Field>
            <Field label={t.grade}><select value={form.grade} onChange={(e) => onChange("grade", e.target.value)} className="input">{Array.from({ length: 8 }, (_, i) => <option value={i + 5} key={i}>Grade {i + 5}</option>)}</select></Field>
            <Field label={t.subject}><select value={form.subject} onChange={(e) => onChange("subject", e.target.value)} className="input">{subjects.map((s) => <option key={s}>{s}</option>)}</select></Field>
            {form.subject === "Other" && <Field label={t.subjectOther} className="sm:col-span-2"><input value={customSubject} onChange={(e) => setCustomSubject(e.target.value)} className="input" placeholder="Enter your subject" /></Field>}
            <Field label={t.marks}><input type="number" min="1" value={form.total_marks} onChange={(e) => onChange("total_marks", e.target.value)} className="input" /></Field>
            <Field label={t.duration}><input type="number" min="1" value={form.duration_minutes} onChange={(e) => onChange("duration_minutes", e.target.value)} className="input" /></Field>
            <Field label={t.count}><input type="number" min="1" max="100" value={form.question_count} onChange={(e) => onChange("question_count", e.target.value)} className="input" /></Field>
            <Field label={t.difficulty}><select value={form.difficulty} onChange={(e) => onChange("difficulty", e.target.value)} className="input">{["Easy", "Medium", "Hard", "Mixed"].map((d) => <option key={d}>{d}</option>)}</select></Field>
            <Field label={t.language}><select value={form.language} onChange={(e) => onChange("language", e.target.value)} className="input"><option>Khmer</option><option>English</option></select></Field>
          </div>
          <div className="mt-5"><label className="mb-2 block text-[11px] font-bold text-slate-600">{t.types}</label><div className="flex flex-wrap gap-2">{questionTypes.map((type) => <button type="button" key={type} onClick={() => toggleType(type)} className={cx("rounded-lg border px-3 py-2 text-[10px] font-semibold transition", form.question_types.includes(type) ? "border-indigo-200 bg-indigo-50 text-indigo-700" : "border-slate-200 text-slate-500 hover:bg-slate-50")}><span className="mr-1.5">{form.question_types.includes(type) ? "✓" : "+"}</span>{type}</button>)}</div></div>
        </div>
        <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-card md:p-7">
          <div className="mb-4 flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-50 text-emerald-600"><BookOpen size={17} /></span><div><h3 className="text-sm font-bold text-ink">{t.chooseLesson}</h3><p className="text-[10px] text-slate-400">Questions are generated from this source only</p></div></div>
          <select value={lessonId} onChange={(e) => setLessonId(e.target.value)} className="input">{!lessons.length && <option value="">No lessons uploaded</option>}{lessons.map((lesson) => <option value={lesson.id} key={lesson.id}>{lesson.filename}</option>)}</select>
          {!lessons.length && <button onClick={onUpload} className="mt-3 text-[11px] font-bold text-indigo-600">Upload a lesson first <ArrowRight size={12} className="inline" /></button>}
        </div>
      </div>
      <div className="h-fit rounded-2xl border border-indigo-100 bg-gradient-to-b from-indigo-50/80 to-white p-5 shadow-card">
        <div className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-indigo-600 text-white"><Sparkles size={18} /></div><h3 className="text-sm font-bold text-ink">Ready to create</h3><p className="mt-1 text-xs leading-5 text-slate-500">AI-generated content stays grounded in your uploaded lesson. Review and approve before sharing with students.</p>
        <div className="my-5 space-y-3 border-y border-indigo-100 py-4 text-[11px] text-slate-600">
          <SummaryRow label={t.grade} value={`Grade ${form.grade}`} /><SummaryRow label={t.subject} value={form.subject === "Other" ? customSubject || "—" : form.subject} /><SummaryRow label={t.questions} value={form.question_count} /><SummaryRow label={t.total} value={`${form.total_marks} marks`} />
          <SummaryRow label="Lesson" value={selectedLesson?.filename || "Not selected"} />
        </div>
        {!selectedLesson && <Button variant="secondary" onClick={onUpload} className="mb-3 w-full" icon={Upload}>Upload a lesson to continue</Button>}
        <Button onClick={onGenerate} disabled={busy === "generate" || !lessonId || !form.question_types.length} className="w-full" icon={busy === "generate" ? LoaderCircle : Sparkles}>{busy === "generate" ? t.generating : t.generateBtn}</Button>
        <p className="mt-3 text-center text-[10px] leading-4 text-slate-400">All generated content is a draft for teacher review.</p>
      </div>
    </div>
  </div>;
}
function Field({ label, children, className = "" }) { return <div className={className}><label className="mb-1.5 block text-[11px] font-bold text-slate-600">{label}</label>{children}</div>; }
function SummaryRow({ label, value }) { return <div className="flex items-center justify-between gap-2"><span className="text-slate-500">{label}</span><span className="truncate font-bold text-ink">{value}</span></div>; }

function PreviewPage({ t, exam, activeTab, setActiveTab, editing, setEditing, busy, sumMarks, onPatch, onSave, onRegenerate, onRegenerateKey, onDownload, onAdd, onRemove }) {
  return <div><SectionTitle eyebrow="REVIEW & APPROVE" title={exam.title} description={`Grade ${exam.grade} · ${exam.subject} · ${exam.duration_minutes} minutes`}
      action={<div className="flex gap-2"><Button variant="secondary" onClick={() => onDownload(activeTab === "key" ? "answer_key" : "paper", "docx")} icon={ArrowDownToLine}>{t.download} DOCX</Button><Button onClick={() => onDownload(activeTab === "key" ? "answer_key" : "paper", "pdf")} icon={ArrowDownToLine}>{t.download} PDF</Button></div>} />
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 bg-white px-4 py-3 shadow-card">
      <div className="flex gap-1 rounded-lg bg-slate-100 p-1"><button onClick={() => setActiveTab("paper")} className={cx("rounded-md px-3 py-1.5 text-[11px] font-bold", activeTab === "paper" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500")}>{t.paper}</button><button onClick={() => setActiveTab("key")} className={cx("rounded-md px-3 py-1.5 text-[11px] font-bold", activeTab === "key" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500")}>{t.answerKey}</button></div>
      <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-500"><span className={cx("flex items-center gap-1", sumMarks === Number(exam.total_marks) ? "text-emerald-600" : "text-rose-600")}><CheckCircle2 size={14} />{sumMarks} / {exam.total_marks} marks</span><span>{exam.questions.length} questions</span><span>{exam.duration_minutes} min</span></div>
      <div className="flex gap-2"><Button variant="secondary" onClick={onRegenerateKey} disabled={busy === "answer-key"} icon={RefreshCw}>{busy === "answer-key" ? "Updating..." : "Regenerate key"}</Button><Button onClick={onSave} disabled={busy === "save"} icon={Check}>{busy === "save" ? "Saving..." : t.save}</Button></div>
    </div>
    <div className="mx-auto max-w-[850px] rounded-2xl border border-slate-200 bg-white px-6 py-8 shadow-card md:px-14 md:py-12">
      <div className="border-b border-slate-200 pb-5 text-center"><p className="text-[10px] font-bold uppercase tracking-[.18em] text-indigo-600">{activeTab === "paper" ? t.paper : t.answerKey}</p><h2 className={cx("mt-3 text-xl font-extrabold text-ink", exam.language === "Khmer" && "khmer")}>{exam.title}</h2><p className="mt-2 text-xs text-slate-500">{exam.subject} · Grade {exam.grade}</p>
        <div className="mt-4 flex justify-center gap-5 text-[10px] font-semibold text-slate-500"><span>Total: {exam.total_marks} marks</span><span>Duration: {exam.duration_minutes} minutes</span></div>
        {activeTab === "paper" && <p className="mt-4 border-t border-dashed border-slate-200 pt-3 text-left text-[11px] text-slate-500">Name: ______________________________ &nbsp; Class: __________ &nbsp; Date: __________</p>}
      </div>
      <div className="divide-y divide-slate-100">{exam.questions.map((question, index) => <QuestionCard key={`${exam.id}-${index}`} t={t} question={question} index={index} isKey={activeTab === "key"} editing={editing === index} setEditing={(value) => setEditing(value ? index : -1)} busy={busy === `question-${index}`} onPatch={onPatch} onRegenerate={onRegenerate} onRemove={onRemove} />)}</div>
      <div className="mt-5 flex flex-wrap justify-between gap-3 border-t border-slate-100 pt-5 no-print"><Button variant="secondary" onClick={onAdd} icon={Plus}>{t.addQuestion}</Button><span className="self-center text-[10px] text-slate-400">{t.original} · Teacher review required</span></div>
      {sumMarks !== Number(exam.total_marks) && <p className="mt-4 rounded-lg bg-rose-50 p-3 text-xs text-rose-700">Marks must total {exam.total_marks} before saving or exporting.</p>}
    </div>
  </div>;
}
function QuestionCard({ t, question, index, isKey, editing, setEditing, busy, onPatch, onRegenerate, onRemove }) {
  return <article className="group py-5"><div className="flex items-start gap-3"><span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-slate-100 text-[11px] font-bold text-slate-600">{index + 1}</span><div className="min-w-0 flex-1">
    {editing ? <div className="space-y-2"><textarea value={question.text} onChange={(e) => onPatch(index, "text", e.target.value)} className="input min-h-[72px]" placeholder="Question text" /><select className="input" value={question.difficulty} onChange={(e) => onPatch(index, "difficulty", e.target.value)}>{["Easy", "Medium", "Hard"].map((v) => <option key={v}>{v}</option>)}</select><input type="number" min="1" className="input w-32" value={question.marks} onChange={(e) => onPatch(index, "marks", Number(e.target.value))} aria-label="Marks" />
      {question.type === "Multiple Choice" && <textarea className="input min-h-[70px]" value={(question.options || []).join("\n")} onChange={(e) => onPatch(index, "options", e.target.value.split("\n"))} placeholder={t.options} />}
      <textarea className="input min-h-[60px]" value={question.answer} onChange={(e) => onPatch(index, "answer", e.target.value)} placeholder={t.answer} /><textarea className="input min-h-[50px]" value={question.explanation || ""} onChange={(e) => onPatch(index, "explanation", e.target.value)} placeholder={t.explanation} /><textarea className="input min-h-[50px]" value={question.rubric || ""} onChange={(e) => onPatch(index, "rubric", e.target.value)} placeholder={t.rubric} />
      <Button variant="secondary" onClick={() => setEditing(false)} icon={Check}>Done editing</Button></div> : <>
      <div className="flex flex-wrap items-center gap-2"><span className="rounded-md bg-indigo-50 px-2 py-1 text-[9px] font-bold text-indigo-700">{question.type}</span><span className="rounded-md bg-slate-50 px-2 py-1 text-[9px] text-slate-500">{question.difficulty}</span><span className="ml-auto text-[10px] font-bold text-slate-500">{question.marks} marks</span></div>
      <p className={cx("mt-2 whitespace-pre-wrap text-[13px] leading-6 text-ink", question.text.match(/[\u1780-\u17ff]/) && "khmer")}>{question.text || <span className="italic text-slate-400">Enter a question...</span>}</p>
      {!isKey && question.options?.length > 0 && <div className="mt-2 grid gap-1.5 sm:grid-cols-2">{question.options.map((option, i) => <p key={i} className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600"><b className="mr-2 text-slate-400">{String.fromCharCode(65 + i)}.</b>{option}</p>)}</div>}
      {isKey && <div className="mt-3 rounded-xl bg-emerald-50/70 p-3"><p className={cx("text-xs font-semibold text-emerald-800", question.answer.match(/[\u1780-\u17ff]/) && "khmer")}>{t.answer}: {question.answer || "—"}</p>{question.explanation && <p className="mt-1 text-[11px] leading-5 text-slate-600">{t.explanation}: {question.explanation}</p>}{question.rubric && <p className="mt-1 text-[11px] leading-5 text-slate-600">{t.rubric}: {question.rubric}</p>}</div>}
      {!isKey && <div className="mt-2 flex items-center gap-1 opacity-100 transition md:opacity-0 md:group-hover:opacity-100 no-print"><button onClick={() => setEditing(true)} className="rounded-md px-2 py-1 text-[10px] font-semibold text-slate-500 hover:bg-slate-100">{t.edit}</button><button disabled={busy} onClick={() => onRegenerate(index)} className="flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-semibold text-indigo-600 hover:bg-indigo-50">{busy ? <LoaderCircle size={11} className="animate-spin" /> : <RefreshCw size={11} />}{t.regenerate}</button><button onClick={() => onRemove(index)} className="rounded-md px-2 py-1 text-[10px] font-semibold text-rose-500 hover:bg-rose-50">{t.remove}</button></div>}
    </>}</div></div></article>;
}

function ChatPage({ t, messages, value, setValue, onSend, endRef, busy, onGenerate }) {
  return <div><SectionTitle eyebrow="AI TEACHING ASSISTANT" title={t.chat} description={t.chatIntro} />
    <div className="mx-auto flex h-[min(680px,calc(100vh-220px))] min-h-[430px] max-w-[850px] flex-col overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-card">
      <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4"><div className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-600 text-white"><Sparkles size={17} /></div><div><p className="text-xs font-bold text-ink">{t.chat}</p><p className="flex items-center gap-1 text-[10px] text-emerald-600"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />Ready to help</p></div><Button onClick={onGenerate} className="ml-auto" icon={Plus}>{t.generateBtn}</Button></div>
      <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50/60 p-5">{messages.map((message, index) => <div key={index} className={cx("flex gap-2.5", message.role === "teacher" && "justify-end")}>{message.role === "assistant" && <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-indigo-100 text-indigo-600"><Sparkles size={13} /></span>}<p className={cx("max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-xs leading-6", message.role === "teacher" ? "rounded-br-md bg-indigo-600 text-white" : "rounded-bl-md border border-slate-100 bg-white text-slate-700 shadow-sm", message.text.match(/[\u1780-\u17ff]/) && "khmer")}>{message.text}</p></div>)}<div ref={endRef} /></div>
      <form onSubmit={onSend} className="flex gap-2 border-t border-slate-100 bg-white p-4"><input value={value} onChange={(e) => setValue(e.target.value)} placeholder={t.chatPlaceholder} className="input flex-1" disabled={busy} /><Button disabled={busy} icon={busy ? LoaderCircle : ArrowRight}>{busy ? "..." : t.send}</Button></form>
    </div>
  </div>;
}

export default App;
