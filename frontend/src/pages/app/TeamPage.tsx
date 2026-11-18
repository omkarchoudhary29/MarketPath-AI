import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { Users, Plus, Shield, Mail, CheckCircle2, Trash2, Copy, Clock, Send, AlertCircle } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';

interface PendingInvite {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
  expires_at: string;
  invite_link?: string;
}

export const TeamPage: React.FC = () => {
  const { addToast } = useApp();
  const { activeOrg, role: currentUserRole } = useAuth();
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [loading, setLoading] = useState(false);

  const [members, setMembers] = useState([
    { id: '1', name: 'Ananya Deshmukh', email: 'ananya.deshmukh@auraterra.in', role: 'owner', active: 'Now' },
    { id: '2', name: 'Vikram Joshi', email: 'vikram.growth@auraterra.in', role: 'marketer', active: '2h ago' },
    { id: '3', name: 'Priya Mehta', email: 'priya.consulting@agency.in', role: 'viewer', active: '1d ago' },
  ]);

  const [invitations, setInvitations] = useState<PendingInvite[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('marketer');
  const [submittingInvite, setSubmittingInvite] = useState(false);
  const [lastCreatedLink, setLastCreatedLink] = useState<string | null>(null);

  // Fetch pending invitations
  const fetchInvitations = async () => {
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      const resp = await fetch('/api/v1/team/invitations', { headers });
      if (resp.ok) {
        const data = await resp.json();
        setInvitations(data);
      }
    } catch (err) {
      console.warn('Failed to fetch pending invitations:', err);
    }
  };

  useEffect(() => {
    fetchInvitations();
  }, [activeOrg?.id]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingInvite(true);

    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) credentials: headers['X-Organization-Id'] = activeOrg.id;

      const resp = await fetch('/api/v1/team/invitations', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          email: inviteEmail.trim().toLowerCase(),
          role: inviteRole.toLowerCase(),
        }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to create team invitation');
      }

      const newInvite = await resp.json();
      setLastCreatedLink(newInvite.invite_link || null);
      setInvitations([newInvite, ...invitations]);

      addToast({
        type: 'success',
        title: 'Invitation Created',
        message: `Invitation generated for ${inviteEmail} with role "${inviteRole}".`,
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Invitation Failed',
        message: err.message || 'Could not send invitation.',
      });
    } finally {
      setSubmittingInvite(false);
    }
  };

  const handleRevoke = async (inviteId: string) => {
    try {
      const token = localStorage.getItem('marketpath_auth_token');
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (activeOrg?.id) headers['X-Organization-Id'] = activeOrg.id;

      const resp = await fetch(`/api/v1/team/invitations/${inviteId}`, {
        method: 'DELETE',
        headers,
      });

      if (resp.ok) {
        setInvitations(invitations.filter((inv) => inv.id !== inviteId));
        addToast({ type: 'info', title: 'Invitation Revoked' });
      }
    } catch (err) {
      addToast({ type: 'error', title: 'Failed to Revoke' });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    addToast({
      type: 'success',
      title: 'Link Copied',
      message: 'Invitation link copied to clipboard.',
    });
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600">Access Governance</span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal tracking-tight mt-0.5">
            Team Members & Role Permissions
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Invite colleagues, assign RBAC roles, and govern access across catalogue, AI copy, campaign budgets, and billing.
          </p>
        </div>

        <button
          onClick={() => {
            setLastCreatedLink(null);
            setShowInviteModal(true);
          }}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-xs cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Invite Team Member
        </button>
      </div>

      {/* Active Members Table */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-charcoal">Active Members ({members.length})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-500 uppercase font-semibold text-[10px]">
              <tr>
                <th className="py-3 px-5">User</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Last Active</th>
                <th className="py-3 px-5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {members.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/60">
                  <td className="py-3 px-5">
                    <span className="font-bold text-charcoal block">{m.name}</span>
                    <span className="text-slate-400 text-[11px] font-mono">{m.email}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full capitalize ${
                        m.role === 'owner'
                          ? 'bg-forest/10 text-forest border border-forest/20'
                          : m.role === 'marketer'
                          ? 'bg-brand-50 text-brand-700 border border-brand-200'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500">{m.active}</td>
                  <td className="py-3 px-5 text-right">
                    {m.role !== 'owner' && (
                      <button
                        onClick={() => {
                          setMembers(members.filter((mem) => mem.id !== m.id));
                          addToast({ type: 'info', title: 'Member Access Revoked' });
                        }}
                        className="text-slate-400 hover:text-rose-600 p-1"
                        title="Remove Member"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pending Invitations Table */}
      <div className="bg-white rounded-3xl border border-slate-200/90 shadow-2xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-500" />
            <h3 className="text-sm font-bold text-charcoal">Pending Invitations ({invitations.length})</h3>
          </div>
          <span className="text-[11px] text-slate-400">Tokens expire after 7 days</span>
        </div>

        {invitations.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No pending invitations. Click "Invite Team Member" above to generate a secure invitation link.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-500 uppercase font-semibold text-[10px]">
                <tr>
                  <th className="py-3 px-5">Invitee Email</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Expires</th>
                  <th className="py-3 px-5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {invitations.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/60">
                    <td className="py-3 px-5 font-mono text-[11px] text-charcoal font-medium">
                      {inv.email}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full capitalize bg-brand-50 text-forest border border-brand-200">
                        {inv.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                        Pending
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 text-[11px]">
                      {new Date(inv.expires_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-5 text-right space-x-2">
                      {inv.invite_link && (
                        <button
                          onClick={() => copyToClipboard(inv.invite_link!)}
                          className="text-brand-600 hover:text-brand-700 p-1 font-semibold text-[11px] inline-flex items-center gap-1"
                          title="Copy Link"
                        >
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </button>
                      )}
                      <button
                        onClick={() => handleRevoke(inv.id)}
                        className="text-slate-400 hover:text-rose-600 p-1"
                        title="Revoke Invitation"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Role Permissions Matrix */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/90 shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-charcoal">Role Permissions Matrix</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-softbeige border border-bordergrey space-y-1.5">
            <span className="font-bold text-forest uppercase tracking-wider text-[11px]">Owner</span>
            <p className="text-mutedgrey text-[11px]">Full organization ownership: Billing, subscription upgrades, team invitations, channel OAuth tokens.</p>
          </div>
          <div className="p-4 rounded-xl bg-softbeige border border-bordergrey space-y-1.5">
            <span className="font-bold text-brand-600 uppercase tracking-wider text-[11px]">Admin</span>
            <p className="text-mutedgrey text-[11px]">Operational control: Manage products, publish listings, edit campaigns; cannot delete organization.</p>
          </div>
          <div className="p-4 rounded-xl bg-softbeige border border-bordergrey space-y-1.5">
            <span className="font-bold text-emerald uppercase tracking-wider text-[11px]">Marketer</span>
            <p className="text-mutedgrey text-[11px]">Content & Campaigns: Create master SKUs, generate AI copy, preview social posts, draft briefs.</p>
          </div>
          <div className="p-4 rounded-xl bg-softbeige border border-bordergrey space-y-1.5">
            <span className="font-bold text-charcoal uppercase tracking-wider text-[11px]">Viewer</span>
            <p className="text-mutedgrey text-[11px]">Strict read-only access: View catalogue, live publishing statuses, and unified analytics reporting.</p>
          </div>
        </div>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <Modal
          isOpen={showInviteModal}
          onClose={() => {
            setShowInviteModal(false);
            setLastCreatedLink(null);
          }}
          title="Invite New Team Member"
          subtitle="Generate a private invitation link for your workspace"
        >
          {lastCreatedLink ? (
            <div className="space-y-4 text-xs">
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Invitation link generated successfully! Share this link with your team member.</span>
              </div>
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Invitation Link</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={lastCreatedLink}
                    className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono"
                  />
                  <button
                    onClick={() => copyToClipboard(lastCreatedLink)}
                    className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold shrink-0 inline-flex items-center gap-1.5"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy</span>
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">
                  The invitee will be prompted to set their own private password upon opening the link.
                </p>
              </div>
              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowInviteModal(false);
                    setLastCreatedLink(null);
                  }}
                  className="px-5 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-charcoal font-bold"
                >
                  Done
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleInvite} className="space-y-4 text-xs">
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="colleague@yourbrand.com or name@gmail.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-charcoal mb-1">Select Role *</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white"
                >
                  <option value="admin">Admin (Operational Control & Listings)</option>
                  <option value="marketer">Marketer (Catalogue & AI Studio)</option>
                  <option value="viewer">Viewer (Read-Only Analytics)</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingInvite}
                  className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold disabled:opacity-50 inline-flex items-center gap-1.5"
                >
                  {submittingInvite ? (
                    <span className="inline-block animate-spin">⌛</span>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Create Invitation Link</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </div>
  );
};
