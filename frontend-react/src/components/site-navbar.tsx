import { useEffect, useRef, useState } from 'react';
import { BookMarked, Github, LogOut, Radio, Shield } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { fetchOnlineCount, sendHeartbeat } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { navigate, useAppLocation } from '@/lib/router';
import { getUserId } from '@/lib/storage';

export function SiteNavbar() {
  const location = useAppLocation();
  const { user, logout } = useAuth();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [onlineCount, setOnlineCount] = useState(0);
  const lastScrollYRef = useRef(0);
  const isPaperPage = location.pathname.startsWith('/papers/');

  useEffect(() => {
    const handleScroll = () => {
      const current = window.scrollY;
      if (current > 100) {
        setIsScrolled(true);
        if (isPaperPage) {
          setIsVisible(false);
        } else {
          setIsVisible(current < lastScrollYRef.current);
        }
      } else {
        setIsScrolled(false);
        setIsVisible(true);
      }
      lastScrollYRef.current = current;
    };

    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isPaperPage]);

  useEffect(() => {
    let mounted = true;

    const syncPresence = async () => {
      try {
        const userId = getUserId();
        await sendHeartbeat(userId);
        const count = await fetchOnlineCount();
        if (mounted) {
          setOnlineCount(count);
        }
      } catch {
        if (mounted) {
          setOnlineCount(0);
        }
      }
    };

    void syncPresence();
    const interval = window.setInterval(() => {
      void syncPresence();
    }, 15000);

    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, [user?.id]);

  return (
    <header
      className={`fixed left-0 right-0 top-0 z-50 transition-all duration-500 ${
        isScrolled
          ? isVisible
            ? 'translate-y-0 border-b border-white/60 bg-white/75 shadow-sm backdrop-blur-xl'
            : '-translate-y-full'
          : 'bg-transparent'
      }`}
    >
      <div className="mx-auto flex max-w-[104rem] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="group flex items-center gap-3"
        >
          <img
            src="/images/logo.svg"
            alt="Paper Insight logo"
            className="h-11 w-11 rounded-2xl object-contain shadow-sm transition-transform duration-300 group-hover:scale-[1.04]"
          />
          <div className="text-left">
            <div className="font-semibold tracking-tight text-[#1b2333]">Paper Insight</div>
            <div className="text-xs text-[#728095]">AI-driven paper analysis</div>
          </div>
        </button>

        <div className="flex items-center gap-2">
          <div className="hidden shrink-0 items-center gap-2 rounded-full bg-white/80 px-4 py-2 text-sm text-[#586578] shadow-sm ring-1 ring-black/5 md:flex">
            <Radio className="h-4 w-4 text-[#16a34a]" />
            <span>{onlineCount} 人在线</span>
          </div>
          {user ? (
            <>
              <Button
                variant="outline"
                className="rounded-full border-[#bfdbfe] bg-[#eff6ff] text-[#2563eb]"
                onClick={() => navigate('/me')}
              >
                <BookMarked className="mr-2 h-4 w-4" />
                我的论文
              </Button>
              {user.role === 'admin' ? (
                <Button
                  variant="outline"
                  className="rounded-full border-[#fed7aa] bg-[#fff7ed] text-[#c2410c]"
                  onClick={() => navigate('/admin')}
                >
                  <Shield className="mr-2 h-4 w-4" />
                  后台
                </Button>
              ) : null}
              <div className="hidden max-w-[14rem] truncate rounded-full bg-white/80 px-4 py-2 text-sm text-[#586578] shadow-sm ring-1 ring-black/5 lg:block">
                {user.email}
              </div>
              <Button
                variant="outline"
                className="rounded-full border-[#d7dde8] bg-[#f8fafc] text-[#243047]"
                onClick={() => void logout()}
              >
                <LogOut className="mr-2 h-4 w-4" />
                退出
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                className="rounded-full border-[#fed7aa] bg-[#fff7ed] text-[#c2410c]"
                onClick={() => navigate('/login')}
              >
                登录
              </Button>
              <Button
                className="rounded-full bg-gradient-to-r from-[#ff9900] to-[#ff7a00] text-white"
                onClick={() => navigate('/register')}
              >
                注册
              </Button>
            </>
          )}
          <Button
            variant="outline"
            className="rounded-full border-[#f3d7df] bg-[#fff6f8] text-[#d84b72] hover:border-[#edbfd0] hover:bg-[#ffeef3] hover:text-[#c93c64]"
            onClick={() => window.open('https://www.xiaohongshu.com/user/profile/63c2055e000000002502c58c', '_blank', 'noopener,noreferrer')}
          >
            小红书
          </Button>
          <Button
            variant="outline"
            className="rounded-full border-[#d7dde8] bg-[#f8fafc] text-[#243047] hover:border-[#c6d0de] hover:bg-[#eef2f7] hover:text-[#162033]"
            onClick={() => window.open('https://github.com/KMnO4-zx/paper_online', '_blank', 'noopener,noreferrer')}
          >
            <Github className="mr-2 h-4 w-4" />
            GitHub
          </Button>
        </div>
      </div>
    </header>
  );
}
