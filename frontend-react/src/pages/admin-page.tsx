import { useCallback, useEffect, useState } from 'react';
import { Copy, Loader2, RefreshCcw, Shield, Ticket, Trash2, Users } from 'lucide-react';
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  changePassword,
  createAdminInvitationCode,
  deleteAdminInvitationCode,
  deleteAdminUser,
  fetchAdminInvitationCodes,
  fetchAdminOnlineMetrics,
  fetchAdminUsers,
  resetAdminUserPassword,
  updateAdminUser,
} from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { navigate } from '@/lib/router';
import type { AdminInvitationCode, AdminOnlineMetrics, AdminUser, AdminUserListResponse } from '@/types';

export function AdminPage() {
  const { user, isLoading } = useAuth();
  const [range, setRange] = useState<'24h' | '7d'>('24h');
  const [metrics, setMetrics] = useState<AdminOnlineMetrics | null>(null);
  const [users, setUsers] = useState<AdminUserListResponse | null>(null);
  const [invitationCodes, setInvitationCodes] = useState<AdminInvitationCode[]>([]);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isGeneratingInvitation, setIsGeneratingInvitation] = useState(false);
  const [invitationMaxUses, setInvitationMaxUses] = useState('1');
  const [generatedInvitationCode, setGeneratedInvitationCode] = useState<string | null>(null);
  const [invitationMessage, setInvitationMessage] = useState<string | null>(null);
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
      const [nextMetrics, nextUsers, nextInvitationCodes] = await Promise.all([
        fetchAdminOnlineMetrics(range),
        fetchAdminUsers(page, search),
        fetchAdminInvitationCodes(),
      ]);
      setMetrics(nextMetrics);
      setUsers(nextUsers);
      setInvitationCodes(nextInvitationCodes.codes);
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
    setError(null);
    try {
      await updateAdminUser(target.id, { is_active: !target.is_active });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新用户状态失败');
    }
  };

  const resetPassword = async (target: AdminUser) => {
    const nextPassword = window.prompt(`输入 ${target.email} 的新密码（至少 8 位）`);
    if (!nextPassword) {
      return;
    }
    setError(null);
    try {
      await resetAdminUserPassword(target.id, nextPassword);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : '重置密码失败');
    }
  };

  const deleteUser = async (target: AdminUser) => {
    setError(null);
    try {
      await deleteAdminUser(target.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除用户失败');
    }
  };

  const generateInvitationCode = async () => {
    const maxUses = Number(invitationMaxUses);
    if (!Number.isInteger(maxUses) || maxUses < 1 || maxUses > 10000) {
      setError('邀请码可使用次数必须是 1 到 10000 之间的整数');
      return;
    }

    setError(null);
    setInvitationMessage(null);
    setIsGeneratingInvitation(true);
    try {
      const payload = await createAdminInvitationCode(maxUses);
      setGeneratedInvitationCode(payload.code);
      setInvitationMessage('邀请码已生成，完整值也会保存在下方列表中。');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成邀请码失败');
    } finally {
      setIsGeneratingInvitation(false);
    }
  };

  const copyInvitationCode = async () => {
    if (!generatedInvitationCode) {
      return;
    }
    try {
      await navigator.clipboard.writeText(generatedInvitationCode);
      setInvitationMessage('邀请码已复制');
    } catch {
      setInvitationMessage('复制失败，请手动选中邀请码复制');
    }
  };

  const deleteInvitationCode = async (target: AdminInvitationCode) => {
    setError(null);
    try {
      await deleteAdminInvitationCode(target.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除邀请码失败');
    }
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
        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Ticket className="h-5 w-5 text-[#ff7a00]" />
              <h2 className="text-xl font-semibold text-[#172033]">邀请码管理</h2>
            </div>
            <p className="mt-1 text-sm text-[#728095]">
              新用户注册必须使用邀请码。只有管理员可以在这里查看和生成完整邀请码。
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              type="number"
              min={1}
              max={10000}
              value={invitationMaxUses}
              onChange={(event) => setInvitationMaxUses(event.target.value)}
              placeholder="可使用次数"
              className="h-10 w-full rounded-full bg-[#f8fafc] sm:w-36"
            />
            <Button
              className="rounded-full bg-gradient-to-r from-[#ff9900] to-[#ff7a00] text-white"
              onClick={() => void generateInvitationCode()}
              disabled={isGeneratingInvitation}
            >
              {isGeneratingInvitation ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              生成邀请码
            </Button>
          </div>
        </div>

        {generatedInvitationCode ? (
          <div className="mb-4 rounded-2xl bg-[#fff7ed] p-4 ring-1 ring-[#fed7aa]">
            <div className="text-sm font-medium text-[#9a3412]">新邀请码</div>
            <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <code className="rounded-xl bg-white px-3 py-2 font-mono text-sm text-[#172033] ring-1 ring-[#fed7aa]">
                {generatedInvitationCode}
              </code>
              <Button variant="outline" className="rounded-full" onClick={() => void copyInvitationCode()}>
                <Copy className="mr-2 h-4 w-4" />
                复制
              </Button>
            </div>
            {invitationMessage ? <div className="mt-2 text-sm text-[#9a3412]">{invitationMessage}</div> : null}
          </div>
        ) : null}

        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-[#eef2f7] text-[#728095]">
              <tr>
                <th className="py-3">邀请码</th>
                <th>状态</th>
                <th>使用次数</th>
                <th>创建者</th>
                <th>创建时间</th>
                <th>最近使用</th>
                <th className="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {invitationCodes.length === 0 ? (
                <tr>
                  <td className="py-4 text-[#728095]" colSpan={7}>暂无邀请码</td>
                </tr>
              ) : (
                invitationCodes.map((code) => {
                  const exhausted = code.used_count >= code.max_uses;
                  return (
                    <tr key={code.id} className="border-b border-[#f1f5f9]">
                      <td className="py-3 font-mono font-medium text-[#172033]">
                        {code.code_text ?? `${code.code_prefix}...`}
                      </td>
                      <td>
                        {!code.is_active ? (
                          <span className="text-[#b91c1c]">已停用</span>
                        ) : exhausted ? (
                          <span className="text-[#c2410c]">已用完</span>
                        ) : (
                          <span className="text-[#16a34a]">可用</span>
                        )}
                      </td>
                      <td>{code.used_count} / {code.max_uses}</td>
                      <td>{code.created_by_email ?? '-'}</td>
                      <td>{new Date(code.created_at).toLocaleString()}</td>
                      <td>{code.last_used_at ? new Date(code.last_used_at).toLocaleString() : '-'}</td>
                      <td className="text-right">
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="outline"
                              size="sm"
                              className="rounded-full border-[#fecdd3] bg-[#fff1f2] text-[#be123c] hover:border-[#fda4af] hover:bg-[#ffe4e6] hover:text-[#9f1239]"
                            >
                              <Trash2 className="mr-1 h-4 w-4" />
                              删除
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>确认删除邀请码？</AlertDialogTitle>
                              <AlertDialogDescription>
                                将删除邀请码 {code.code_text ?? `${code.code_prefix}...`} 的记录。已注册用户不受影响，但该邀请码不能再用于注册。
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel className="rounded-full">取消</AlertDialogCancel>
                              <AlertDialogAction
                                className="rounded-full bg-[#e11d48] text-white hover:bg-[#be123c]"
                                onClick={() => void deleteInvitationCode(code)}
                              >
                                确认删除
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
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
          <table className="w-full min-w-[860px] text-left text-sm">
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
                  <td className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" className="rounded-full" onClick={() => void toggleUserActive(target)}>
                        {target.is_active ? '停用' : '启用'}
                      </Button>
                      <Button variant="outline" size="sm" className="rounded-full" onClick={() => void resetPassword(target)}>
                        重置密码
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-full border-[#fecdd3] bg-[#fff1f2] text-[#be123c] hover:border-[#fda4af] hover:bg-[#ffe4e6] hover:text-[#9f1239]"
                            disabled={target.id === user?.id}
                            title={target.id === user?.id ? '不能删除当前登录管理员' : undefined}
                          >
                            <Trash2 className="mr-1 h-4 w-4" />
                            删除
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>确认删除用户？</AlertDialogTitle>
                            <AlertDialogDescription>
                              将删除 {target.email} 的账号、登录会话、论文标记和已归属的聊天记录。此操作无法撤销。
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel className="rounded-full">取消</AlertDialogCancel>
                            <AlertDialogAction
                              className="rounded-full bg-[#e11d48] text-white hover:bg-[#be123c]"
                              onClick={() => void deleteUser(target)}
                            >
                              确认删除
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
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
