import { useState } from "react";
import { BookOpen, LoaderCircle } from "lucide-react";
import { useAuth } from "./AuthContext";
import { supabase } from "./supabaseClient";

export default function AuthForm({ initialError = "" }) {
  const { setAuthNotice } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initialError);
  const [message, setMessage] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (mode === "signup" && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      const credentials = { email: email.trim(), password };
      const { data, error: authError } = mode === "signup"
        ? await supabase.auth.signUp(credentials)
        : await supabase.auth.signInWithPassword(credentials);

      if (authError) {
        setError(authError.message);
      } else if (mode === "signup") {
        const successMessage = data.session
          ? "Account created. You are now signed in."
          : "Account created. Check your email to confirm before logging in.";
        setMessage(successMessage);
        if (data.session) setAuthNotice(successMessage);
      }
    } catch (authError) {
      setError(authError.message || "Authentication failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  function toggleMode(event) {
    event.preventDefault();
    setMode((current) => current === "login" ? "signup" : "login");
    setConfirmPassword("");
    setError("");
    setMessage("");
  }

  const signingUp = mode === "signup";

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-5 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-100 bg-white p-7 shadow-card md:p-9">
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-indigo-600 text-white"><BookOpen size={21} /></div>
          <div><p className="text-lg font-extrabold text-ink">ExamGen <span className="text-indigo-600">AI</span></p><p className="text-[10px] font-semibold tracking-[.15em] text-slate-400">KHMER EDUCATION</p></div>
        </div>
        <h1 className="text-xl font-extrabold text-ink">{signingUp ? "Create your account" : "Log in"}</h1>
        <p className="mt-2 text-sm text-slate-500">Use your Supabase Auth account to access your exam workspace.</p>
        {error && <div role="alert" className="mt-5 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-xs leading-5 text-rose-700">{error}</div>}
        {message && <div role="status" className="mt-5 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-xs leading-5 text-emerald-700">{message}</div>}
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block text-xs font-semibold text-slate-600">Email
            <input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="input mt-1.5" />
          </label>
          <label className="block text-xs font-semibold text-slate-600">Password
            <input type="password" autoComplete={signingUp ? "new-password" : "current-password"} minLength={6} required value={password} onChange={(event) => setPassword(event.target.value)} className="input mt-1.5" />
          </label>
          {signingUp && (
            <label className="block text-xs font-semibold text-slate-600">Confirm password
              <input type="password" autoComplete="new-password" minLength={6} required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} className="input mt-1.5" />
            </label>
          )}
           <button type="submit" disabled={busy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50">
            {busy && <LoaderCircle size={16} className="animate-spin" />}{busy ? (signingUp ? "Creating account..." : "Logging in...") : (signingUp ? "Sign up" : "Log in")}
          </button>
        </form>
        <p className="mt-5 text-center text-xs text-slate-500">
          {signingUp ? "Already have an account?" : "Need an account?"}{" "}
          <a href="#" onClick={toggleMode} className="font-bold text-indigo-600 hover:text-indigo-700">
            {signingUp ? "Log in" : "Sign up"}
          </a>
        </p>
      </section>
    </main>
  );
}
