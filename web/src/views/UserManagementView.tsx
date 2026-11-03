import React, { useState, useEffect } from 'react';
import { User } from '../types';
import { api } from '../services/api';
import { Shield, PlusCircle, Edit2, Trash2, RefreshCw, Lock, Ban, CheckCircle2 } from 'lucide-react';

export const UserManagementView: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    badge_number: '',
    department: 'Forensic Field Operations',
    role: 'FIELD_OFFICER'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await api.getUsers();
      setUsers(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load users.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleInputChange = (key: string, value: string) => {
    setNewUser({ ...newUser, [key]: value });
    setErrorMessage(null);
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUser.username || !newUser.email || !newUser.password || !newUser.full_name) {
      setErrorMessage('All required fields must be filled.');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.createUser({
        username: newUser.username,
        email: newUser.email,
        password: newUser.password,
        full_name: newUser.full_name,
        badge_number: newUser.badge_number || undefined,
        department: newUser.department,
        role: newUser.role
      });
      setShowAddModal(false);
      setNewUser({
        username: '',
        email: '',
        password: '',
        full_name: '',
        badge_number: '',
        department: 'Forensic Field Operations',
        role: 'FIELD_OFFICER'
      });
      setSuccessMessage('User created successfully.');
      fetchUsers();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create user.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleActive = async (user: User) => {
    if (!window.confirm(`Are you sure you want to ${user.is_active ? 'deactivate' : 'activate'} user ${user.username}?`)) {
      return;
    }
    try {
      await api.toggleUserActive(user.id);
      setSuccessMessage(`User ${user.username} ${user.is_active ? 'deactivated' : 'activated'} successfully.`);
      fetchUsers();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update user status.');
    }
  };

  const roleBadge = (role: string) => {
    const colors: Record<string, string> = {
      ADMIN: '#8B5CF6',
      FIELD_OFFICER: '#3B82F6',
      SUPERVISOR: '#06B6D4',
      AUDITOR: '#10B981'
    };
    return (
      <span style={{
        padding: '4px 10px',
        borderRadius: 'var(--radius-full)',
        fontSize: '0.72rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        fontFamily: 'var(--font-mono)',
        background: `rgba(${colors[role] ? parseInt(colors[role].slice(1), 16) >> 16 : 139},${colors[role] ? (parseInt(colors[role].slice(1), 16) >> 8) & 0xFF : 99},${colors[role] ? parseInt(colors[role].slice(1), 16) & 0xFF : 203},0.15)`,
        color: colors[role] || '#9CA3AF',
        border: `1px solid ${colors[role] || '#9CA3AF'}40`
      }}>
        {role.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>User & Access Management</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Authorized administrator-managed user accounts, roles, and access status.
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary btn-sm"
          >
            <PlusCircle size={15} /> Add User
          </button>
        </div>
      </div>

      {errorMessage && (
        <div style={{
          padding: 12,
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid #EF4444',
          borderRadius: 'var(--radius-sm)',
          color: '#F87171',
          fontSize: '0.82rem'
        }}>
          {errorMessage}
        </div>
      )}

      {successMessage && (
        <div style={{
          padding: 12,
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid #10B981',
          borderRadius: 'var(--radius-sm)',
          color: '#34D399',
          fontSize: '0.82rem'
        }}>
          {successMessage}
        </div>
      )}

      {/* Users Table */}
      <div className="forensic-card" style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Authorized Operators</h2>
          <button onClick={fetchUsers} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <RefreshCw className="animate-spin" size={32} style={{ margin: '0 auto 12px', display: 'block' }} />
            <p>Loading user accounts...</p>
          </div>
        ) : users.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
            <p>No users found.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="forensic-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Full Name</th>
                  <th>Badge / ID</th>
                  <th>Role</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{user.username}</td>
                    <td>{user.full_name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{user.badge_number || 'N/A'}</td>
                    <td>{roleBadge(user.role)}</td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{user.department}</td>
                    <td>
                      <span className={`badge ${user.is_active ? 'badge-verified' : 'badge-tampered'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          onClick={() => handleToggleActive(user)}
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          title={user.is_active ? 'Deactivate Account' : 'Activate Account'}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: 28, maxWidth: 540 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: 16 }}>Register New Field Operator</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 20 }}>
              Accounts are created by administrators. Operators receive credentials through secure channels.
            </p>

            <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label className="forensic-label">Authorized Username</label>
                <input
                  type="text"
                  required
                  className="forensic-input"
                  placeholder="e.g. officer2"
                  value={newUser.username}
                  onChange={(e) => handleInputChange('username', e.target.value)}
                />
              </div>
              <div>
                <label className="forensic-label">Email Address</label>
                <input
                  type="email"
                  required
                  className="forensic-input"
                  placeholder="e.g. officer2@police.gov"
                  value={newUser.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                />
              </div>
              <div>
                <label className="forensic-label">Temporary Password</label>
                <input
                  type="password"
                  required
                  className="forensic-input"
                  placeholder="Minimum 8 characters"
                  value={newUser.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                />
              </div>
              <div>
                <label className="forensic-label">Full Name</label>
                <input
                  type="text"
                  required
                  className="forensic-input"
                  placeholder="e.g. Det. Sarah Chen"
                  value={newUser.full_name}
                  onChange={(e) => handleInputChange('full_name', e.target.value)}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="forensic-label">Badge Number</label>
                  <input
                    type="text"
                    className="forensic-input"
                    placeholder="e.g. DET-8500"
                    value={newUser.badge_number}
                    onChange={(e) => handleInputChange('badge_number', e.target.value)}
                  />
                </div>
                <div>
                  <label className="forensic-label">Department</label>
                  <input
                    type="text"
                    className="forensic-input"
                    value={newUser.department}
                    onChange={(e) => handleInputChange('department', e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="forensic-label">Role / Clearance Level</label>
                <select
                  className="forensic-select"
                  value={newUser.role}
                  onChange={(e) => handleInputChange('role', e.target.value)}
                >
                  <option value="ADMIN">Administrator (Full Control)</option>
                  <option value="FIELD_OFFICER">Field Officer (Create Tests)</option>
                  <option value="SUPERVISOR">Supervisor (Review & Verify)</option>
                  <option value="AUDITOR">Auditor (Evidence Verification)</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? <RefreshCw className="animate-spin" size={14} /> : <CheckCircle2 size={14} />}
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};