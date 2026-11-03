import React, { useState, useEffect } from 'react';
import { Shield, Database, Clock, RefreshCw, CheckCircle2, AlertTriangle, Settings, HardDrive } from 'lucide-react';
import { api } from '../services/api';

export const SystemSettingsView: React.FC = () => {
  const [health, setHealth] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchHealth = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSystemSettings();
      setHealth(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load system health.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
        <RefreshCw className="animate-spin" size={32} style={{ margin: '0 auto 12px', display: 'block' }} />
        <p>Querying system health...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Shield size={24} color="#06B6D4" />
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>System Configuration & Health</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              System version, algorithm version, signing key status, and storage health.
            </p>
          </div>
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

      {/* System Overview */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>System Overview</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          <div style={{ background: 'rgba(17, 24, 39, 0.6)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <Settings size={16} color="#60A5FA" />
              <span style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>System Version</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', fontWeight: 700 }}>{health?.system_version || 'N/A'}</div>
          </div>
          <div style={{ background: 'rgba(17, 24, 39, 0.6)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <Shield size={16} color="#06B6D4" />
              <span style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Algorithm Version</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', fontWeight: 700 }}>{health?.algorithm_version || 'N/A'}</div>
          </div>
          <div style={{ background: 'rgba(17, 24, 39, 0.6)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <HardDrive size={16} color="#8B5CF6" />
              <span style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Signing Key ID</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700 }}>{health?.signing_key_id || 'N/A'}</div>
          </div>
          <div style={{ background: 'rgba(17, 24, 39, 0.6)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <Database size={16} color="#34D399" />
              <span style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Database Status</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', fontWeight: 700, color: '#34D399' }}>
              {health?.database_connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </div>

      {/* Storage Health */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Evidence Storage Health</h2>
        {health?.storage ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
            <div style={{ background: 'rgba(17, 24, 39, 0.6)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: 6 }}>
                Upload Path
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', wordBreak: 'break-all' }}>{health.storage.upload_path}</div>
            </div>
            <div style={{ background: 'rgba(17, 24, 39, 0.6)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Total Storage</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{health.storage.total_gb} GB</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Free Storage</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#34D399' }}>{health.storage.free_gb} GB</span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
            <p>Storage information unavailable.</p>
          </div>
        )}
      </div>

      {/* Public Key for Audit */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Active Ed25519 Public Key</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              For judicial and defense audit verification of evidence signatures.
            </p>
          </div>
          <button onClick={fetchHealth} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
        {health?.public_key_hex ? (
          <div>
            <div style={{
              background: 'rgba(255, 255, 255, 0.04)',
              padding: 14,
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.7rem',
              color: '#93C5FD',
              wordBreak: 'break-all',
              border: '1px solid var(--border-subtle)'
            }}>
              {health.public_key_hex}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 6 }}>
              Algorithm: <b>{health.algorithm || 'Ed25519'}</b> | Key ID: <b>{health.key_id || 'KEY-FORENSIC-2026-V1'}</b>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-dim)' }}>
            <p>Public key information unavailable.</p>
          </div>
        )}
      </div>

      {/* Security Notice */}
      <div className="forensic-card" style={{
        padding: 24,
        border: '1px solid rgba(239, 68, 68, 0.3)',
        background: 'rgba(239, 68, 68, 0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 12 }}>
          <AlertTriangle size={20} color="#EF4444" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: 4 }}>Prototype Security Notice</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0 }}>
              This prototype stores the Ed25519 private key on the server filesystem for demonstration purposes.
              In production, use a managed key service (AWS KMS, Azure Key Vault, HashiCorp Vault, or HSM).
              Never commit private keys to source control.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};