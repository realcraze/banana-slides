import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { getAuthMe } from '@/api/endpoints';
import { Button, Loading } from '@/components/shared';
import type { AuthMe } from '@/types';
import { Globe, LockKeyhole, RefreshCw, ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface AuthContextValue {
  me: AuthMe;
  loading: boolean;
  reload: () => Promise<void>;
  isAdmin: boolean;
}

const DEFAULT_ME: AuthMe = {
  authenticated: false,
  role: 'user',
  auth_mode: 'disabled',
  email: null,
  name: null,
  avatar_url: null,
  auth_bypassed: false,
};

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [me, setMe] = useState<AuthMe>(DEFAULT_ME);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getAuthMe();
      setMe(response.data || DEFAULT_ME);
    } catch {
      setMe(DEFAULT_ME);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const value = useMemo<AuthContextValue>(() => ({
    me,
    loading,
    reload,
    isAdmin: me.role === 'admin',
  }), [loading, me, reload]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return value;
}

export const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { me, loading, reload } = useAuth();
  const { i18n } = useTranslation();
  const [signingIn, setSigningIn] = useState(false);
  const isZh = i18n.language?.startsWith('zh');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-primary">
        <Loading message="Checking access..." />
      </div>
    );
  }

  if (me.authenticated) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(255,215,0,0.18),_transparent_34%),radial-gradient(circle_at_left,_rgba(255,228,77,0.14),_transparent_28%),linear-gradient(180deg,_#fffdf7_0%,_#ffffff_52%,_#fffaf0_100%)] dark:bg-[radial-gradient(circle_at_top,_rgba(245,166,35,0.1),_transparent_30%),linear-gradient(180deg,_#14141a_0%,_#13131a_100%)]">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-8">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="蕉幻 Banana Slides Logo" className="h-11 w-11 object-contain" />
            <div className="space-y-0.5">
              <div className="text-lg font-semibold text-gray-900 dark:text-foreground-primary">
                {isZh ? '蕉幻' : 'Banana Slides'}
              </div>
              <div className="text-xs text-gray-500 dark:text-foreground-tertiary">
                {isZh ? '企业演示文稿工作台' : 'Enterprise presentation workspace'}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-white/70 bg-white/75 px-3 py-1.5 text-xs text-gray-600 shadow-sm backdrop-blur md:flex dark:border-border-primary dark:bg-background-secondary/75 dark:text-foreground-secondary">
              <ShieldCheck size={14} className="text-banana-600 dark:text-banana" />
              {isZh ? '已启用企业身份校验' : 'Enterprise identity required'}
            </div>
            <button
              onClick={() => i18n.changeLanguage(isZh ? 'en' : 'zh')}
              className="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-gray-600 transition-all hover:bg-banana-100/60 hover:text-gray-900 dark:text-foreground-tertiary dark:hover:bg-background-hover dark:hover:text-gray-100"
              title={isZh ? '界面语言' : 'Interface Language'}
            >
              <Globe size={14} />
              <span>{isZh ? 'EN' : '中'}</span>
            </button>
          </div>
        </header>

        <main className="flex flex-1 items-center justify-center py-10">
          <section className="relative flex min-h-[400px] w-full max-w-[380px] overflow-hidden rounded-[30px] border border-white bg-[linear-gradient(180deg,_rgba(255,255,255,0.96)_0%,_rgba(255,252,241,0.92)_100%)] p-6 shadow-[0_24px_60px_rgba(77,55,0,0.12),0_8px_24px_rgba(255,199,0,0.18),inset_0_1px_0_rgba(255,255,255,0.95)] ring-1 ring-yellow-100/80 backdrop-blur dark:border-border-primary dark:bg-background-secondary/88 dark:shadow-[0_24px_60px_rgba(0,0,0,0.28),inset_0_1px_0_rgba(255,255,255,0.06)] dark:ring-border-primary sm:min-h-[450px] sm:p-8">
            <div className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-banana-300/80 to-transparent" />
            <div className="pointer-events-none absolute -right-16 -top-16 h-36 w-36 rounded-full bg-banana-200/35 blur-3xl" />
            <div className="flex flex-1 flex-col">
              <div className="space-y-6">
                <div className="inline-flex items-center gap-2 rounded-full border border-orange-100 bg-banana-50 px-3 py-1.5 text-xs font-medium text-gray-700 dark:border-border-primary dark:bg-background-primary/70 dark:text-foreground-secondary">
                  <LockKeyhole size={14} className="text-orange-500" />
                  {isZh ? '公司 Microsoft 账号登录' : 'Company Microsoft sign-in'}
                </div>

                <div className="space-y-3">
                  <h1 className="text-2xl font-semibold tracking-tight text-gray-900 dark:text-foreground-primary">
                    {isZh ? '登录后进入蕉幻工作台' : 'Sign in to continue to Banana Slides'}
                  </h1>
                  <p className="text-sm leading-6 text-gray-500 dark:text-foreground-secondary">
                    {isZh
                      ? '把一句想法变成高颜值可编辑 PPT，从大纲、配图到导出一气呵成，让团队少熬夜、多出漂亮成片。'
                      : 'Turn a rough idea into a polished, editable deck, from outline and visuals to export, so teams ship sharper, better-looking slides faster.'}
                  </p>
                </div>
              </div>

              <div className="mt-auto space-y-4 pt-10">
                <Button
                  className="w-full disabled:hover:translate-y-0 disabled:hover:shadow-md"
                  disabled={signingIn}
                  loading={signingIn}
                  onClick={() => {
                    setSigningIn(true);
                    window.location.assign(`/oauth2/start?rd=${encodeURIComponent('/')}`);
                  }}
                  icon={<LockKeyhole size={16} />}
                >
                  {signingIn
                    ? (isZh ? '正在跳转 Microsoft 登录...' : 'Redirecting to Microsoft...')
                    : (isZh ? '使用 Microsoft 账号登录' : 'Sign in with Microsoft')}
                </Button>
                <Button
                  variant="secondary"
                  className="w-full"
                  disabled={signingIn}
                  onClick={() => reload()}
                  icon={<RefreshCw size={16} />}
                >
                  {isZh ? '重新检查访问状态' : 'Retry access check'}
                </Button>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading, isAdmin } = useAuth();

  if (loading) {
    return null;
  }

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
