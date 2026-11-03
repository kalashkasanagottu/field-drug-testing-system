import React from 'react';
import { 
  Shield, Camera, Database, FileCheck, Sliders, History, 
  Wifi, WifiOff, Smartphone, Monitor, UserCheck, LogOut, AlertTriangle, Settings, FileText
} from 'lucide-react';
import { User, UserRole } from '../types';

interface NavbarProps {
  currentUser: User | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isHandheldMode: boolean;
  setIsHandheldMode: (val: boolean) => void;
  isSimulatedOffline: boolean;
  setIsSimulatedOffline: (val: boolean) => void;
  pendingSyncCount: number;
  onQuickRoleSwitch: (role: UserRole) => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  activeTab,
  setActiveTab,
  isHandheldMode,
  setIsHandheldMode,
  isSimulatedOffline,
  setIsSimulatedOffline,
  pendingSyncCount,
  onQuickRoleSwitch,
  onLogout
}) => {
  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(11, 15, 25, 0.95)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '12px 24px'
    }}>
      <div style={{
        maxWidth: 1600,
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16
      }}>
        {/* Brand & Node Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            width: 42,
            height: 42,
            borderRadius: 10,
            background: 'linear-gradient(135deg, #06B6D4 0%, #2563EB 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(6, 182, 212, 0.35)'
          }}>
            <Shield size={24} color="#FFF" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.02em' }}>
                DIGITAL FORENSIC FIELD TEST
              </span>
              <span className="badge badge-verified" style={{ fontSize: '0.65rem', padding: '2px 8px' }}>
                ED25519 SEALED
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
              CIELAB ΔE₀₀ Calibrated • ISO Presumptive Analysis
            </p>
          </div>
        </div>

        {/* Primary Navigation */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`btn btn-sm ${activeTab === 'dashboard' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Monitor size={15} /> Dashboard
          </button>
          
          <button
            onClick={() => setActiveTab('capture')}
            className={`btn btn-sm ${activeTab === 'capture' ? 'btn-cyan' : 'btn-secondary'}`}
            style={{ fontWeight: 700 }}
          >
            <Camera size={15} /> Field Capture
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`btn btn-sm ${activeTab === 'history' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Database size={15} /> Test History
          </button>

          <button
            onClick={() => setActiveTab('verification')}
            className={`btn btn-sm ${activeTab === 'verification' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <FileCheck size={15} /> Verifier
          </button>

          {(currentUser?.role === 'ADMIN' || currentUser?.role === 'SUPERVISOR') && (
            <button
              onClick={() => setActiveTab('kits')}
              className={`btn btn-sm ${activeTab === 'kits' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <Sliders size={15} /> Kits & Profiles
            </button>
          )}

          {(currentUser?.role === 'ADMIN') && (
            <button
              onClick={() => setActiveTab('users')}
              className={`btn btn-sm ${activeTab === 'users' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <UserCheck size={15} /> Users
            </button>
          )}

          {(currentUser?.role === 'ADMIN') && (
            <button
              onClick={() => setActiveTab('calibration')}
              className={`btn btn-sm ${activeTab === 'calibration' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <Sliders size={15} /> Calibration
            </button>
          )}

          {(currentUser?.role === 'ADMIN' || currentUser?.role === 'AUDITOR') && (
            <button
              onClick={() => setActiveTab('audit')}
              className={`btn btn-sm ${activeTab === 'audit' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <History size={15} /> Audit Chain
            </button>
          )}

          {(currentUser?.role === 'ADMIN') && (
            <button
              onClick={() => setActiveTab('settings')}
              className={`btn btn-sm ${activeTab === 'settings' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <Settings size={15} /> System Settings
            </button>
          )}

          <button
            onClick={() => setActiveTab('reports')}
            className={`btn btn-sm ${activeTab === 'reports' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <FileText size={15} /> Reports
          </button>

          <button
            onClick={() => setActiveTab('sync')}
            className={`btn btn-sm ${activeTab === 'sync' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ position: 'relative' }}
          >
            {isSimulatedOffline ? <WifiOff size={15} color="#F87171" /> : <Wifi size={15} color="#34D399" />}
            Sync
            {pendingSyncCount > 0 && (
              <span style={{
                background: '#EF4444',
                color: '#FFF',
                borderRadius: '9999px',
                fontSize: '0.65rem',
                padding: '1px 6px',
                fontWeight: 700,
                marginLeft: 4
              }}>
                {pendingSyncCount}
              </span>
            )}
          </button>
        </nav>

        {/* View Controls & User Information */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Offline Mode Toggle */}
          <button
            onClick={() => setIsSimulatedOffline(!isSimulatedOffline)}
            className="btn btn-secondary btn-sm"
            title="Toggle simulated field offline state without internet"
            style={{
              borderColor: isSimulatedOffline ? '#EF4444' : 'rgba(255,255,255,0.12)',
              color: isSimulatedOffline ? '#FCA5A5' : 'var(--text-muted)'
            }}
          >
            {isSimulatedOffline ? <WifiOff size={14} /> : <Wifi size={14} />}
            {isSimulatedOffline ? 'Offline Mode' : 'Online'}
          </button>

          {/* Mobile Handheld Device View Toggle */}
          <button
            onClick={() => setIsHandheldMode(!isHandheldMode)}
            className={`btn btn-sm ${isHandheldMode ? 'btn-primary' : 'btn-secondary'}`}
            title="Toggle between handheld mobile phone mode and widescreen desktop station"
          >
            {isHandheldMode ? <Smartphone size={14} /> : <Monitor size={14} />}
            {isHandheldMode ? 'Mobile View' : 'Desktop View'}
          </button>

          {/* User Badge & Quick Role Selector */}
          {currentUser && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 8, borderLeft: '1px solid var(--border-subtle)' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 700 }}>{currentUser.full_name}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                  {currentUser.role} • {currentUser.badge_number || 'ID-00'}
                </div>
              </div>

              {/* Quick Role Switcher Dropdown */}
              <select
                value={currentUser.role}
                onChange={(e) => onQuickRoleSwitch(e.target.value as UserRole)}
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: 'var(--text-main)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 6,
                  padding: '4px 6px',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)'
                }}
                title="Switch demo role instantly"
              >
                <option value="ADMIN">Admin (Full Control)</option>
                <option value="FIELD_OFFICER">Field Officer</option>
                <option value="SUPERVISOR">Supervisor</option>
                <option value="AUDITOR">Auditor</option>
              </select>

              <button
                onClick={onLogout}
                className="btn btn-secondary btn-sm"
                title="Sign out"
                style={{ padding: '6px' }}
              >
                <LogOut size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
