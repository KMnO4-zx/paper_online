import { useCallback, useEffect, useState } from 'react';
import { Loader2, RefreshCcw, Shield, Users } from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  changePassword,
  fetchAdminOnlineMetrics,
  fetchAdminUsers,
  resetAdminUserPassword,
  updateAdminUser,
} from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { navigate } from '@/lib/router';
import type { AdminOnlineMetrics, AdminUser, AdminUserListResponse } from '@/types';

export function AdminPage() {
  const { user, isLoading } = useAuth();
  const [range, setRange] = useState<'24h' | '7d'>('24h');
  const [metrics, setMetrics] = useState<AdminOnlineMetrics | null>(null);
  const [users, setUsers] = useState<AdminUserListResponse | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

  const canAccess = user?.role === 'admin';

  const load = useCallback(async () => {
    if (!canAccess) {
      return;
    }
    setIsRefreshing(true);
    setError(null);
    try {
      const [nextMetrics, nextUsers] = await Promise.all([
        fetchAdminOnlineMetrics(range),
        fetchAdminUsers(page, search),
      ]);
      setMetrics(nextMetrics);
      setUsers(nextUsers);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setIsRefreshing(false);
    }
  }, [canAccess, page, range, search]);

  useEffect(() => {
    void load();
  }, [load]);

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-5xl items-center gap-2 rounded-[32px] bg-white p-8 text-[#728095]">
        <Loader2 className="h-5 w-5 animate-spin" />
        加载账号状态...
      </div>
    );
  }

  if (!canAccess) {
    return (
      <div className="mx-auto max-w-2xl rounded-[32px] bg-white p-8 shadow-sm ring-1 ring-black/5">
        <h1 className="text-2xl font-semibold text-[#172033]">需要管理员权限</h1>
        <p className="mt-3 text-sm leading-6 text-[#728095]">请使用管理员账号登录后访问后台。</p>
        <Button className="mt-6 rounded-full" onClick={() => navigate('/login')}>去登录</Button>
      </div>
    );
  }

  const submitPasswordChange = async () => {
    setPasswordMessage(null);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setPasswordMessage('密码已更新');
    } catch (err) {
      setPasswordMessage(err instanceof Error ? err.message : '密码更新失败');
    }
  };

  const toggleUserActive = async (target: AdminUser) => {
    await updateAdminUser(target.id, { is_active: !target.is_active });
    await load();
  };

  const resetPassword = async (target: AdminUser) => {
    const nextPassword = window.prompt(`输入 ${target.email} 的新密码（至少 8 位）`);
    if (!nextPassword) {
      return;
    }
    await resetAdminUserPassword(target.id, nextPassword);
    await load();
  };

  return (
    <div className="mx-auto max-w-7xl animate-fade-in space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-[#172033]">管理员后台</h1>
          <p className="mt-1 text-sm text-[#728095]">在线趋势、用户管理和管理员密码维护。</p>
        </div>
        <Button variant="outline" className="rounded-full" onClick={() => void load()} disabled={isRefreshing}>
          {isRefreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCcw className="mr-2 h-4 w-4" />}
          刷新
        </Button>
      </div>

      {error ? <div className="rounded-2xl bg-[#fff1f2] p-4 text-sm text-[#b91c1c]">{error}</div> : null}

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
          <div className="flex items-center gap-2 text-sm text-[#728095]">
            <Users className="h-4 w-4 text-[#16a34a]" />
            当前在线
          </div>
          <div className="mt-3 text-3xl font-semibold text-[#172033]">{metrics?.current.count ?? 0}</div>
        </div>
        <div className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
          <div className="text-sm text-[#728095]">登录用户</div>
          <div className="mt-3 text-3xl font-semibold text-[#2563eb]">{metrics?.current.authenticated_count ?? 0}</div>
        </div>
        <div className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-black/5">
          <div className="text-sm text-[#728095]">游客</div>
          <div className="mt-3 text-3xl font-semibold text-[#ff7a00]">{metrics?.current.guest_count ?? 0}</div>
        </div>
      </section>

      <section className="rounded-[32px] bg-white p-6 shadow-sm ring-1 ring-black/5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-[#172033]">在线人数趋势</h2>
          <div className="flex gap-2">
            {(['24h', '7d'] as const).map((item) => (
              <Button
                key={item}
                variant={range === item ? 'default' : 'outline'}
                className="rounded-full"
                onClick={() => setRange(item)}
              >
                {item === '24h' ? '24 小时' : '7 天'}
              </Button>
            ))}
          </div>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metrics?.trend ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="bucket_at" tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} />
              <YAxis allowDecimals={false} />
              <Tooltip labelFormatter={(value) => new Date(String(value)).toLocaleString()} />
              <Line type="monotone" dataKey="count" stroke="#ff7a00" strokeWidth={2} dot={false} name="总在线" />
              <Line type="monotone" dataKey="authenticated_count" stroke="#2563eb" strokeWidth={2} dot={false} name="登录用户" />
              <Line type="monotone" dataKey="guest_count" stroke="#16a34a" strokeWidth={2} dot={false} name="游客" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-[32px] bg-white p-6 shadow-sm ring-1 ring-black/5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-xl font-semibold text-[#172033]">用户管理</h2>
          <div className="flex gap-2">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="搜索邮箱"
              className="h-10 rounded-full bg-[#f8fafc]"
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  setPage(1);
                  void load();
                }
              }}
            />
            <Button variant="outline" className="rounded-full" onClick={() => { setPage(1); void load(); }}>
              搜索
            </Button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-[#eef2f7] text-[#728095]">
              <tr>
                <th className="py-3">邮箱</th>
                <th>角色</th>
                <th>状态</th>
                <th>注册时间</th>
                <th>最近登录</th>
                <th className="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {(users?.users ?? []).map((target) => (
                <tr key={target.id} className="border-b border-[#f1f5f9]">
                  <td className="py-3 font-medium text-[#172033]">{target.email}</td>
                  <td>{target.role === 'admin' ? '管理员' : '用户'}</td>
                  <td>{target.is_active ? '启用' : '停用'}</td>
                  <td>{new Date(target.created_at).toLocaleDateString()}</td>
                  <td>{target.last_login_at ? new Date(target.last_login_at).toLocaleString() : '-'}</td>
                  <td className="space-x-2 text-right">
                    <Button variant="outline" size="sm" className="rounded-full" onClick={() => void toggleUserActive(target)}>
                      {target.is_active ? '停用' : '启用'}
                    </Button>
                    <Button variant="outline" size="sm" className="rounded-full" onClick={() => void resetPassword(target)}>
                      重置密码
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex items-center justify-end gap-2">
          <Button variant="outline" className="rounded-full" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>
            上一页
          </Button>
          <span className="text-sm text-[#728095]">{users?.page ?? page} / {users?.pages ?? 1}</span>
          <Button variant="outline" className="rounded-full" disabled={page >= (users?.pages ?? 1)} onClick={() => setPage((current) => current + 1)}>
            下一页
          </Button>
        </div>
      </section>

      <section className="rounded-[32px] bg-white p-6 shadow-sm ring-1 ring-black/5">
        <div className="mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5 text-[#ff7a00]" />
          <h2 className="text-xl font-semibold text-[#172033]">修改管理员密码</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
          <Input
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            placeholder="当前密码"
            className="h-11 rounded-2xl bg-[#f8fafc]"
          />
          <Input
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            placeholder="新密码"
            className="h-11 rounded-2xl bg-[#f8fafc]"
          />
          <Button className="rounded-2xl" onClick={() => void submitPasswordChange()}>更新密码</Button>
        </div>
        {passwordMessage ? <div className="mt-3 text-sm text-[#728095]">{passwordMessage}</div> : null}
      </section>
    </div>
  );
}
