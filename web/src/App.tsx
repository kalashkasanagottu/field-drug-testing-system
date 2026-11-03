import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './views/DashboardView';
import { FieldCaptureWizard } from './views/FieldCaptureWizard';
import { TestHistoryView } from './views/TestHistoryView';
import { VerificationPortalView } from './views/VerificationPortalView';
import { KitManagementView } from './views/KitManagementView';
import { AuditLogsView } from './views/AuditLogsView';
import { OfflineSyncView } from './views/OfflineSyncView';
import { TestDetailModal } from './views/TestDetailModal';
import { LoginView } from './views/LoginView';
import { UserManagementView } from './views/UserManagementView';
import { CalibrationProfileManagementView } from './views/CalibrationProfileManagementView';
import { SystemSettingsView } from './views/SystemSettingsView';
import { ReportsView } from './views/ReportsView';
import { User, TestKit, DashboardStats, UserRole } from './types';
import { api } from './services/api';
import { offlineStorage } from './services/offlineStorage';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isHandheldMode, setIsHandheldMode] = useState(false);
  const [isSimulatedOffline, setIsSimulatedOffline] = useState(false);
  const [selectedTestId, setSelectedTestId] = useState<string | null>(null);

  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [kits, setKits] = useState<TestKit[]>([]);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [pendingSyncCount, setPendingSyncCount] = useState(0);

  // Initialize Auth & Kits
  useEffect(() => {
    const init = async () => {
      try {
        const user = await api.getCurrentUser();
        setCurrentUser(user);
        await refreshKitsAndStats();
      } catch (err) {
        console.warn('Session expired or not authenticated:', err);
        setCurrentUser(null);
      } finally {
        setIsInitializing(false);
      }
    };
    init();
  }, []);

  const refreshKitsAndStats = async () => {
    setIsLoadingStats(true);
    try {
      const [statsData, kitsData] = await Promise.all([
        api.getDashboardStats().catch(() => null),
        api.getKits().catch(() => [])
      ]);
      if (statsData) setDashboardStats(statsData);
      if (kitsData) setKits(kitsData);

      const queue = offlineStorage.getQueuedTests();
      setPendingSyncCount(queue.filter(t => t.status === 'SAVED_LOCALLY' || t.status === 'FAILED').length);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingStats(false);
    }
  };

  const handleQuickRoleSwitch = async (role: UserRole) => {
    let u = 'admin';
    let p = 'AdminPass123!';
    if (role === 'FIELD_OFFICER') { u = 'officer1'; p = 'OfficerPass123!'; }
    if (role === 'SUPERVISOR') { u = 'supervisor1'; p = 'SupervisorPass123!'; }
    if (role === 'AUDITOR') { u = 'auditor1'; p = 'AuditorPass123!'; }

    try {
      const data = await api.login(u, p);
      setCurrentUser({
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
      refreshKitsAndStats();
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = async () => {
    await api.logout();
    setCurrentUser(null);
  };

  if (isInitializing) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Initializing Forensic Node...</p>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <LoginView
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          refreshKitsAndStats();
        }}
      />
    );
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <DashboardView
            stats={dashboardStats}
            isLoading={isLoadingStats}
            onNavigate={setActiveTab}
            onSelectTest={setSelectedTestId}
            onRefresh={refreshKitsAndStats}
          />
        );
      case 'capture':
        return (
          <FieldCaptureWizard
            kits={kits}
            onTestComplete={(testId) => {
              setSelectedTestId(testId);
              refreshKitsAndStats();
            }}
            isOffline={isSimulatedOffline}
          />
        );
      case 'history':
        return (
          <TestHistoryView
            kits={kits}
            onSelectTest={setSelectedTestId}
          />
        );
      case 'verification':
        return (
          <VerificationPortalView
            onSelectTest={setSelectedTestId}
          />
        );
      case 'kits':
        return (
          <KitManagementView
            kits={kits}
            onRefreshKits={refreshKitsAndStats}
          />
        );
      case 'audit':
        return <AuditLogsView />;
      case 'sync':
        return (
          <OfflineSyncView
            isOffline={isSimulatedOffline}
            setIsOffline={setIsSimulatedOffline}
            onRefreshStats={refreshKitsAndStats}
            onSelectTest={setSelectedTestId}
          />
        );
      case 'users':
        return <UserManagementView />;
      case 'calibration':
        return <CalibrationProfileManagementView />;
      case 'settings':
        return <SystemSettingsView />;
      case 'reports':
        return <ReportsView />;
      default:
        return null;
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isHandheldMode={isHandheldMode}
        setIsHandheldMode={setIsHandheldMode}
        isSimulatedOffline={isSimulatedOffline}
        setIsSimulatedOffline={setIsSimulatedOffline}
        pendingSyncCount={pendingSyncCount}
        onQuickRoleSwitch={handleQuickRoleSwitch}
        onLogout={handleLogout}
      />

      <main style={{ flex: 1, padding: isHandheldMode ? '20px 10px' : '28px 24px' }}>
        {isHandheldMode ? (
          /* Mobile Handheld Device Frame Simulator */
          <div style={{
            maxWidth: 430,
            margin: '0 auto',
            border: '12px solid #1E293B',
            borderRadius: 48,
            overflow: 'hidden',
            boxShadow: '0 25px 60px -15px rgba(0,0,0,0.8), 0 0 30px rgba(6,182,212,0.15)',
            background: 'var(--bg-primary)',
            minHeight: 840,
            position: 'relative'
          }}>
            {/* Simulated Phone Notch / Speaker */}
            <div style={{
              width: 140,
              height: 22,
              background: '#1E293B',
              borderRadius: '0 0 14px 14px',
              margin: '0 auto 12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{ width: 44, height: 4, background: '#334155', borderRadius: 2 }} />
            </div>

            <div style={{ padding: 12 }}>
              {renderContent()}
            </div>
          </div>
        ) : (
          <div style={{ maxWidth: 1600, margin: '0 auto' }}>
            {renderContent()}
          </div>
        )}
      </main>

      {/* Forensic Evidence Detail Modal */}
      {selectedTestId && (
        <TestDetailModal
          testId={selectedTestId}
          onClose={() => setSelectedTestId(null)}
          onRefreshList={refreshKitsAndStats}
        />
      )}
    </div>
  );
};

export default App;
