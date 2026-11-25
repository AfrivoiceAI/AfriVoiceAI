import { useEffect, useState, type FormEvent } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  History,
  Image,
  LayoutDashboard,
  LogOut,
  Mic,
  Sparkles,
  Wand2,
} from 'lucide-react';
import { api, getToken } from './api';

type User = {
  id: string;
  email: string;
  display_name: string;
};

type CreationKind = 'text' | 'speech' | 'image';
type AuthMode = 'register' | 'login';

type GenerationOutput = {
  status?: string;
  text?: string;
  message?: string;
  media_url?: string;
  model?: string;
};

type Generation = {
  id: string;
  kind: string;
  prompt: string;
  output?: GenerationOutput;
  created_at?: string;
};

type Usage = {
  used: number;
  limit: number;
};

type AuthResponse = {
  access_token: string;
  user: User;
};

const generationKinds: Array<{
  id: CreationKind;
  label: string;
  description: string;
  Icon: typeof Sparkles;
}> = [
  { id: 'text', label: 'Text', description: 'Ideas into words', Icon: Sparkles },
  { id: 'speech', label: 'Voice', description: 'Words into audio', Icon: Mic },
  { id: 'image', label: 'Image', description: 'Ideas into visuals', Icon: Image },
];

const promptLabels: Record<CreationKind, string> = {
  text: 'What would you like to create?',
  speech: 'What should your voiceover say?',
  image: 'Describe the image you have in mind',
};

const promptPlaceholders: Record<CreationKind, string> = {
  text: 'A warm, memorable welcome message for a neighbourhood food business in Lagos…',
  speech: 'Write or paste the words you want to hear spoken…',
  image: 'A lively market at golden hour, with rich green and warm gold details…',
};

function readStoredUser(): User | null {
  try {
    const stored = localStorage.getItem('av_user');
    if (!stored) return null;

    const value: unknown = JSON.parse(stored);
    if (
      typeof value === 'object' &&
      value !== null &&
      'id' in value &&
      'email' in value &&
      'display_name' in value &&
      typeof value.id === 'string' &&
      typeof value.email === 'string' &&
      typeof value.display_name === 'string'
    ) {
      return {
        id: value.id,
        email: value.email,
        display_name: value.display_name,
      };
    }
  } catch {
    return null;
  }

  return null;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}

function initials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] ?? '')
    .join('')
    .toUpperCase();
}

function formatDate(value?: string): string {
  if (!value) return 'Just now';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Recently';

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(date);
}

function mediaUrl(path: string): string {
  const apiBase = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1')
    .replace(/\/+$/, '')
    .replace(/\/api\/v1$/, '');
  return `${apiBase}${path}`;
}

function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand-lockup${compact ? ' brand-lockup-compact' : ''}`}>
      <span className="brand-mark" aria-hidden="true">
        <span>A</span>
        <span>V</span>
      </span>
      <span className="brand-name">
        AfriVoice<span>AI</span>
      </span>
    </div>
  );
}

function AuthScreen({
  onAuthenticated,
}: {
  onAuthenticated: (user: User) => void;
}) {
  const [mode, setMode] = useState<AuthMode>('register');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      const body =
        mode === 'register'
          ? { email, password, display_name: name }
          : { email, password };
      const response = await api<AuthResponse>(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify(body),
      });

      localStorage.setItem('av_token', response.access_token);
      localStorage.setItem('av_user', JSON.stringify(response.user));
      onAuthenticated(response.user);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  const isRegistering = mode === 'register';

  return (
    <main className="auth-page">
      <section className="auth-story" aria-label="About AfriVoiceAI">
        <BrandMark />
        <div className="auth-story-copy">
          <span className="eyebrow eyebrow-on-dark">A CREATIVE SPACE FOR AFRICAN VOICES</span>
          <h1>
            Your ideas,
            <br />
            <span>made for more.</span>
          </h1>
          <p>
            Find your words, shape your story, and bring your next idea to life.
          </p>
        </div>
        <div className="story-art" aria-hidden="true">
          <div className="story-orbit story-orbit-one" />
          <div className="story-orbit story-orbit-two" />
          <div className="story-sun" />
          <div className="story-card">
            <Sparkles size={17} />
            <span>Made for your next big idea</span>
            <ArrowRight size={16} />
          </div>
        </div>
        <p className="auth-story-footer">CREATE WITH CULTURE. SHARE WITH CONFIDENCE.</p>
      </section>

      <section className="auth-panel">
        <div className="auth-mobile-brand">
          <BrandMark compact />
        </div>
        <div className="auth-form-wrap">
          <span className="eyebrow">{isRegistering ? 'YOUR STUDIO STARTS HERE' : 'WELCOME BACK'}</span>
          <h2>{isRegistering ? 'Create your account' : 'Sign in to your studio'}</h2>
          <p className="auth-intro">
            {isRegistering
              ? 'A little space for all the ideas you’re ready to make real.'
              : 'Pick up where your creativity left off.'}
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {isRegistering && (
              <label className="field" htmlFor="display-name">
                <span>Your name</span>
                <input
                  autoComplete="name"
                  id="display-name"
                  onChange={(event) => setName(event.target.value)}
                  placeholder="e.g. Ada Okafor"
                  required
                  value={name}
                />
              </label>
            )}
            <label className="field" htmlFor="email">
              <span>Email address</span>
              <input
                autoComplete="email"
                id="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                type="email"
                value={email}
              />
            </label>
            <label className="field" htmlFor="password">
              <span>Password</span>
              <input
                autoComplete={isRegistering ? 'new-password' : 'current-password'}
                id="password"
                minLength={8}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 8 characters"
                required
                type="password"
                value={password}
              />
            </label>

            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}

            <button className="button button-primary auth-submit" disabled={busy} type="submit">
              <span>{busy ? 'Please wait…' : isRegistering ? 'Create my account' : 'Sign in'}</span>
              {!busy && <ArrowRight size={17} />}
            </button>
          </form>

          <p className="auth-switch">
            {isRegistering ? 'Already have an account?' : 'New to AfriVoiceAI?'}{' '}
            <button
              className="text-button"
              onClick={() => {
                setMode(isRegistering ? 'login' : 'register');
                setError('');
              }}
              type="button"
            >
              {isRegistering ? 'Sign in' : 'Create an account'}
            </button>
          </p>
          <p className="auth-note">
            <Sparkles aria-hidden="true" size={14} />
            An early preview for ideas in progress.
          </p>
        </div>
      </section>
    </main>
  );
}

function Studio({ user, onSignOut }: { user: User; onSignOut: () => void }) {
  const [kind, setKind] = useState<CreationKind>('text');
  const [prompt, setPrompt] = useState(
    'Create a friendly welcome message for a Nigerian small business.',
  );
  const [language, setLanguage] = useState('en-NG');
  const [result, setResult] = useState<GenerationOutput | null>(null);
  const [history, setHistory] = useState<Generation[]>([]);
  const [usage, setUsage] = useState<Usage>({ used: 0, limit: 30 });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function refreshWorkspace() {
    const [recentGenerations, monthlyUsage] = await Promise.all([
      api<Generation[]>('/generations'),
      api<Usage>('/generations/usage'),
    ]);
    setHistory(recentGenerations);
    setUsage(monthlyUsage);
  }

  useEffect(() => {
    if (!getToken()) return;

    let active = true;
    Promise.all([api<Generation[]>('/generations'), api<Usage>('/generations/usage')])
      .then(([recentGenerations, monthlyUsage]) => {
        if (!active) return;
        setHistory(recentGenerations);
        setUsage(monthlyUsage);
      })
      .catch((requestError: unknown) => {
        if (active) setError(errorMessage(requestError));
      });

    return () => {
      active = false;
    };
  }, []);

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setResult(null);

    try {
      const response = await api<{ output: GenerationOutput }>('/generations', {
        method: 'POST',
        body: JSON.stringify({ kind, prompt, language }),
      });
      setResult(response.output);
      await refreshWorkspace();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  const firstName = user.display_name.trim().split(/\s+/)[0] || 'Creator';
  const usagePercent =
    usage.limit > 0 ? Math.min((usage.used / usage.limit) * 100, 100) : 0;
  const resultImage =
    result?.media_url && /\.(png|jpe?g|webp)$/i.test(result.media_url);

  function chooseKind(nextKind: CreationKind) {
    setKind(nextKind);
    setResult(null);
    setError('');
  }

  return (
    <div className="studio-shell">
      <aside className="sidebar">
        <BrandMark />
        <div className="sidebar-divider" />
        <span className="sidebar-label">YOUR WORKSPACE</span>
        <nav className="sidebar-nav" aria-label="Workspace navigation">
          <a className="sidebar-link active" href="#studio">
            <LayoutDashboard aria-hidden="true" size={18} />
            <span>Studio</span>
            <span className="nav-indicator" />
          </a>
          <a className="sidebar-link" href="#recent">
            <History aria-hidden="true" size={18} />
            <span>Recent creations</span>
          </a>
        </nav>

        <div className="sidebar-spacer" />

        <section className="usage-card" aria-label="Monthly generation usage">
          <div className="usage-heading">
            <span>This month</span>
            <Sparkles aria-hidden="true" size={15} />
          </div>
          <div className="usage-count">
            <strong>{usage.used}</strong>
            <span>of {usage.limit} generations</span>
          </div>
          <div
            aria-label={`${Math.round(usagePercent)} percent of monthly generations used`}
            className="usage-track"
            role="progressbar"
            aria-valuemax={100}
            aria-valuemin={0}
            aria-valuenow={Math.round(usagePercent)}
          >
            <span style={{ width: `${usagePercent}%` }} />
          </div>
          <p>Your creative allowance resets monthly.</p>
        </section>

        <div className="profile-row">
          <span className="avatar">{initials(user.display_name)}</span>
          <span className="profile-copy">
            <strong>{user.display_name}</strong>
            <small>Creator account</small>
          </span>
          <button
            aria-label="Sign out"
            className="icon-button signout-button"
            onClick={onSignOut}
            title="Sign out"
            type="button"
          >
            <LogOut aria-hidden="true" size={17} />
          </button>
        </div>
      </aside>

      <div className="studio-main">
        <header className="topbar">
          <div className="mobile-brand">
            <BrandMark compact />
          </div>
          <nav className="mobile-nav" aria-label="Workspace navigation">
            <a href="#studio">Studio</a>
            <a href="#recent">Recent</a>
          </nav>
          <div className="topbar-status">
            <span className="status-dot" />
            <span>Early access</span>
          </div>
          <div className="topbar-profile">
            <span className="avatar avatar-small">{initials(user.display_name)}</span>
            <span>{firstName}</span>
          </div>
          <button
            aria-label="Sign out"
            className="icon-button mobile-signout"
            onClick={onSignOut}
            title="Sign out"
            type="button"
          >
            <LogOut aria-hidden="true" size={16} />
            <span>Sign out</span>
          </button>
        </header>

        <main className="studio-content" id="studio">
          <section className="welcome-section">
            <div className="welcome-copy">
              <span className="eyebrow">YOUR CREATIVE WORKSPACE</span>
              <h1>
                Good to see you, <span>{firstName}.</span>
              </h1>
              <p>What would you like to bring to life today?</p>
            </div>
            <div className="welcome-seal" aria-hidden="true">
              <span>MADE</span>
              <Sparkles size={19} />
              <span>TO CREATE</span>
            </div>
          </section>

          <div className="studio-grid">
            <section className="card composer-card" aria-labelledby="composer-title">
              <div className="card-heading">
                <div>
                  <span className="eyebrow">CREATE SOMETHING NEW</span>
                  <h2 id="composer-title">Start with an idea</h2>
                </div>
                <span className="preview-badge">
                  <span className="status-dot" />
                  MVP PREVIEW
                </span>
              </div>

              <div className="creation-tabs" role="group" aria-label="Choose what to create">
                {generationKinds.map(({ id, label, description, Icon }) => (
                  <button
                    aria-pressed={kind === id}
                    className={`creation-tab${kind === id ? ' selected' : ''}`}
                    key={id}
                    onClick={() => chooseKind(id)}
                    type="button"
                  >
                    <span className="tab-icon">
                      <Icon aria-hidden="true" size={19} />
                    </span>
                    <span className="tab-copy">
                      <strong>{label}</strong>
                      <small>{description}</small>
                    </span>
                    {kind === id && <span className="tab-check"><CheckCircle2 size={16} /></span>}
                  </button>
                ))}
              </div>

              <form className="composer-form" onSubmit={handleGenerate}>
                <label className="field prompt-field" htmlFor="creation-prompt">
                  <span className="prompt-label-row">
                    <span>{promptLabels[kind]}</span>
                    <span className="optional-label">Be as specific as you like</span>
                  </span>
                  <textarea
                    id="creation-prompt"
                    onChange={(event) => setPrompt(event.target.value)}
                    placeholder={promptPlaceholders[kind]}
                    required
                    rows={6}
                    value={prompt}
                  />
                </label>

                {kind === 'speech' && (
                  <label className="field language-field" htmlFor="creation-language">
                    <span>Voice language</span>
                    <select
                      id="creation-language"
                      onChange={(event) => setLanguage(event.target.value)}
                      value={language}
                    >
                      <option value="en-NG">Nigerian English · experimental</option>
                      <option value="pcm">Nigerian Pidgin · not supported by baseline</option>
                      <option value="yo">Yorùbá · not yet supported</option>
                      <option value="ig">Igbo · not yet supported</option>
                      <option value="ha">Hausa · not yet supported</option>
                      <option value="en">English</option>
                    </select>
                  </label>
                )}

                <div className="composer-actions">
                  <span className="quality-note">
                    <Sparkles aria-hidden="true" size={15} />
                    Model capabilities vary by language.
                  </span>
                  <button className="button button-primary generate-button" disabled={busy} type="submit">
                    {busy ? (
                      <span className="button-spinner" aria-hidden="true" />
                    ) : (
                      <Wand2 aria-hidden="true" size={17} />
                    )}
                    <span>{busy ? 'Creating…' : 'Generate'}</span>
                    {!busy && <ArrowRight aria-hidden="true" size={16} />}
                  </button>
                </div>
              </form>

              {error && (
                <p className="form-error workspace-error" role="alert">
                  {error}
                </p>
              )}

              {result && (
                <section className="result-panel" aria-live="polite">
                  <div className="result-heading">
                    <span className="result-icon">
                      <CheckCircle2 aria-hidden="true" size={17} />
                    </span>
                    <div>
                      <strong>Your creation is ready</strong>
                      <small>
                        {result.status === 'demo' ? 'Demo output' : result.model || 'AI-generated draft'}
                      </small>
                    </div>
                  </div>
                  {result.text && <p className="result-text">{result.text}</p>}
                  {result.message && <p className="result-text">{result.message}</p>}
                  {result.media_url &&
                    (resultImage ? (
                      <img
                        alt="Generated result"
                        className="generated-image"
                        src={mediaUrl(result.media_url)}
                      />
                    ) : (
                      <audio className="generated-audio" controls src={mediaUrl(result.media_url)} />
                    ))}
                </section>
              )}
            </section>

            <aside className="right-rail">
              <section className="idea-card">
                <div className="idea-decoration" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </div>
                <span className="idea-icon">
                  <Sparkles aria-hidden="true" size={18} />
                </span>
                <span className="eyebrow eyebrow-on-dark">A NOTE FOR CREATORS</span>
                <h2>Your voice is the starting point.</h2>
                <p>
                  Use AI as a creative partner. Review every result, then make it unmistakably yours.
                </p>
                <span className="idea-footer">
                  CREATE WITH INTENTION <ArrowRight aria-hidden="true" size={15} />
                </span>
              </section>

              <section className="card recent-card" id="recent" aria-labelledby="recent-title">
                <div className="recent-heading">
                  <div>
                    <span className="eyebrow">PICK UP WHERE YOU LEFT OFF</span>
                    <h2 id="recent-title">Recent creations</h2>
                  </div>
                  <span className="recent-count">{history.length}</span>
                </div>

                {history.length === 0 ? (
                  <div className="empty-history">
                    <span className="empty-history-icon">
                      <History aria-hidden="true" size={20} />
                    </span>
                    <strong>Your ideas will live here</strong>
                    <p>Your latest creations will appear here when you start generating.</p>
                    <a href="#studio">
                      Start creating <ArrowRight aria-hidden="true" size={14} />
                    </a>
                  </div>
                ) : (
                  <ul className="history-list">
                    {history.slice(0, 5).map((item) => (
                      <li className="history-item" key={item.id}>
                        <span className="history-kind-icon">
                          {item.kind === 'speech' ? (
                            <Mic aria-hidden="true" size={17} />
                          ) : item.kind === 'image' ? (
                            <Image aria-hidden="true" size={17} />
                          ) : (
                            <Sparkles aria-hidden="true" size={17} />
                          )}
                        </span>
                        <span className="history-copy">
                          <strong>{item.prompt}</strong>
                          <small>
                            {item.kind} <span>·</span> {formatDate(item.created_at)}
                          </small>
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </aside>
          </div>

          <footer className="studio-footer">
            <span>AfriVoiceAI</span>
            <span>Early MVP · Review AI outputs before publishing.</span>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(readStoredUser);

  function handleSignOut() {
    localStorage.removeItem('av_token');
    localStorage.removeItem('av_user');
    setUser(null);
  }

  if (!user) {
    return <AuthScreen onAuthenticated={setUser} />;
  }

  return <Studio onSignOut={handleSignOut} user={user} />;
}
