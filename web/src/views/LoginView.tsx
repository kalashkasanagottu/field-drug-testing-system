import React, { useState } from 'react';
import { Shield, Lock, User, RefreshCw, Key, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { User as UserType } from '../types';

interface LoginViewProps {
  onLoginSuccess: (user: UserType) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('AdminPass123!');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await api.login(username, password);
      onLoginSuccess({
        id: data.user_id,
        username: data.username,
        email: `${data.username}@forensic.gov`,
        full_name: data.full_name,
        badge_number: data.badge_number,
        department: data.department,
        role: data.role,
        is_active: true,
        created_at: new Date().toISOString()
      });
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickDemoSelect = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 20
    }}>
      <div className="forensic-card" style={{ maxWidth: 460, width: '100%', padding: 36 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 54,
            height: 54,
            borderRadius: 14,
            background: 'linear-gradient(135deg, #06B6D4 0%, #2563EB 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 0 24px rgba(6, 182, 212, 0.4)'
          }}>
            <Shield size={30} color="#FFF" />
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Digital Forensic Field Testing</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 4 }}>
            Tamper-Evident Evidence & Automated Presumptive Analysis
          </p>
        </div>

        {errorMessage && (
          <div style={{
            padding: 12,
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #EF4444',
            borderRadius: 'var(--radius-sm)',
            color: '#F87171',
            fontSize: '0.82rem',
            marginBottom: 16
          }}>
            {errorMessage}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label className="forensic-label">Authorized Username</label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 13 }} />
              <input
                type="text"
                required
                className="forensic-input"
                style={{ paddingLeft: 38 }}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="forensic-label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 13 }} />
              <input
                type="password"
                required
                className="forensic-input"
                style={{ paddingLeft: 38 }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', marginTop: 8 }}
            disabled={isLoading}
          >
            {isLoading ? <RefreshCw className="animate-spin" size={16} /> : <Key size={16} />}
            Authenticate & Open Secure Node
          </button>
        </form>

        {/* 1-Click Demo Accounts Selector */}
        <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid var(--border-subtle)' }}>
          <span className="forensic-label" style={{ textAlign: 'center', marginBottom: 10 }}>
            1-Click Demo Credentials
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <button
              type="button"
              onClick={() => handleQuickDemoSelect('admin', 'AdminPass123!')}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.72rem' }}
            >
              Admin (Chief Forensic)
            </button>
            <button
              type="button"
              onClick={() => handleQuickDemoSelect('officer1', 'OfficerPass123!')}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.72rem' }}
            >
              Field Officer (Det. Miller)
            </button>
            <button
              type="button"
              onClick={() => handleQuickDemoSelect('supervisor1', 'SupervisorPass123!')}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.72rem' }}
            >
              Supervisor (Lt. Vance)
            </button>
            <button
              type="button"
              onClick={() => handleQuickDemoSelect('auditor1', 'AuditorPass123!')}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.72rem' }}
            >
              Auditor (Elena Rostova)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
