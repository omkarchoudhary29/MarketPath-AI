import React, { useEffect, useState } from 'react';
import { Users, Shield, CheckCircle2, RefreshCw, Search, ShieldAlert, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { apiClient } from '../../lib/api';

interface UserItem {
  id: string;
  email: string;
  full_name?: string;
  is_platform_admin: boolean;
  memberships_count: number;
  created_at: string;
}

export const AdminUsersPage: React.FC = () => {
  const { session, user: currentUser } = useAuth();
  const { addToast } = useApp();
  const token = session?.access_token;

  const [users, setUsers] = useState<UserItem[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchUsers = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await apiClient<UserItem[]>('/api/v1/admin/users', { token });
      setUsers(data);
    } catch (err: any) {
      console.error('Failed to load users:', err);
      addToast({
        type: 'error',
        title: 'Failed to Query Users',
        message: err.message || 'Could not fetch platform user registry.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [token]);

  const handleToggleAdminStatus = async (targetUser: UserItem) => {
    if (!token) return;
    const newStatus = !targetUser.is_platform_admin;
    setUpdatingId(targetUser.id);
    try {
      await apiClient(`/api/v1/admin/users/${targetUser.id}/admin-status`, {
        method: 'PATCH',
        token,
        body: JSON.stringify({ is_platform_admin: newStatus }),
      });

      setUsers((prev) =>
        prev.map((u) => (u.id === targetUser.id ? { ...u, is_platform_admin: newStatus } : u))
      );

      addToast({
        type: newStatus ? 'warning' : 'info',
        title: newStatus ? 'Admin Rights Granted' : 'Admin Rights Revoked',
        message: `User ${targetUser.email} is ${newStatus ? 'now a Platform Admin' : 'no longer an operator'}.`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Role Update Failed',
        message: err.message || 'Unable to modify platform admin status.',
      });
    } finally {
      setUpdatingId(null);
    }
  };

  const filtered = users.filter(
    (u) =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.full_name && u.full_name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-rose-400">
            Identity Registry
          </span>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
            Global User Accounts & Operator Roles
          </h1>
        </div>
        <button
          onClick={fetchUsers}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search users by email or full name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-800 bg-slate-900 text-white focus:outline-none focus:ring-1 focus:ring-rose-500 font-mono"
          />
        </div>
      </div>

      <div className="bg-slate-950 rounded-3xl border border-slate-800 overflow-hidden font-mono text-xs">
        <table className="w-full text-left">
          <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
            <tr>
              <th className="py-3 px-5">User & Email</th>
              <th className="py-3 px-4">Joined Date</th>
              <th className="py-3 px-4">Org Memberships</th>
              <th className="py-3 px-4">Platform Role</th>
              <th className="py-3 px-5 text-right">Access Control</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-rose-500" />
                  Loading accounts from database...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  No users match the search criteria.
                </td>
              </tr>
            ) : (
              filtered.map((u) => {
                const isSelf = currentUser?.id === u.id;
                return (
                  <tr key={u.id} className="hover:bg-slate-900/60">
                    <td className="py-3.5 px-5">
                      <span className="font-bold text-white block">
                        {u.full_name || 'Unnamed Seller'}
                        {isSelf && (
                          <span className="ml-2 text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                            You
                          </span>
                        )}
                      </span>
                      <span className="text-slate-400 text-[11px]">{u.email}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {new Date(u.created_at).toLocaleDateString('en-IN', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {u.memberships_count} {u.memberships_count === 1 ? 'Tenant' : 'Tenants'}
                    </td>
                    <td className="py-3.5 px-4">
                      {u.is_platform_admin ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-400 border border-rose-800">
                          <ShieldCheck className="w-3 h-3" />
                          PLATFORM_ADMIN
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] text-slate-400 bg-slate-900 border border-slate-800">
                          Standard Seller
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      <button
                        onClick={() => handleToggleAdminStatus(u)}
                        disabled={updatingId === u.id || isSelf}
                        title={isSelf ? 'Cannot demote yourself' : undefined}
                        className={`px-2.5 py-1 rounded text-[11px] font-medium border transition-colors cursor-pointer ${
                          isSelf
                            ? 'opacity-40 cursor-not-allowed bg-slate-900 text-slate-500 border-slate-800'
                            : u.is_platform_admin
                            ? 'bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border-rose-800/60'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                        }`}
                      >
                        {updatingId === u.id
                          ? 'Updating...'
                          : u.is_platform_admin
                          ? 'Revoke Admin'
                          : 'Promote to Admin'}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
