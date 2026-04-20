import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/lib/auth';
import { navigate } from '@/lib/router';

interface AuthPageProps {
  mode: 'login' | 'register';
}

export function AuthPage({ mode }: AuthPageProps) {
  const { login, register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isRegister = mode === 'register';

  const submit = async () => {
    if (isSubmitting) {
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      if (isRegister) {
        await register(email, password);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[calc(100vh-12rem)] max-w-md items-center">
      <section className="w-full rounded-[32px] bg-white p-8 shadow-sm ring-1 ring-black/5">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-[#172033]">
            {isRegister ? '注册账号' : '登录账号'}
          </h1>
          <p className="mt-2 text-sm leading-6 text-[#728095]">
            登录后可以同步聊天历史、点赞和看过记录，后续推荐系统也会基于这些数据工作。
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#334155]">邮箱</label>
            <Input
              value={email}
              type="email"
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              className="h-11 rounded-2xl bg-[#f8fafc]"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#334155]">密码</label>
            <Input
              value={password}
              type="password"
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="至少 8 个字符"
              className="h-11 rounded-2xl bg-[#f8fafc]"
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  void submit();
                }
              }}
            />
          </div>

          {error ? <div className="rounded-2xl bg-[#fff1f2] p-3 text-sm text-[#b91c1c]">{error}</div> : null}

          <Button
            className="h-11 w-full rounded-2xl bg-gradient-to-r from-[#ff9900] to-[#ff7a00] text-white"
            onClick={() => void submit()}
            disabled={isSubmitting}
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : isRegister ? '注册并登录' : '登录'}
          </Button>
        </div>

        <div className="mt-6 text-center text-sm text-[#728095]">
          {isRegister ? '已有账号？' : '还没有账号？'}
          <button
            type="button"
            className="ml-1 font-medium text-[#ff7a00]"
            onClick={() => navigate(isRegister ? '/login' : '/register')}
          >
            {isRegister ? '去登录' : '去注册'}
          </button>
        </div>
      </section>
    </div>
  );
}
