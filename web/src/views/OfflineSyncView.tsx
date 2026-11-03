import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, Trash2, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';
import { offlineStorage, QueuedTest } from '../services/offlineStorage';

interface OfflineSyncViewProps {
  isOffline: boolean;
  setIsOffline: (val: boolean) => void;
  onRefreshStats: () => void;
  onSelectTest: (testId: string) => void;
}

export const OfflineSyncView: React.FC<OfflineSyncViewProps> = ({
  isOffline,
  setIsOffline,
  onRefreshStats,
  onSelectTest
}) => {
  const [queue, setQueue] = useState<QueuedTest[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState<{ current: number; total: number } | null>(null);

  const reloadQueue = () => {
    setQueue(offlineStorage.getQueuedTests());
  };

  useEffect(() => {
    reloadQueue();
  }, []);

  const handleSyncAll = async () => {
    if (isOffline) {
      alert('Device is currently in offline mode. Disable offline mode to connect to backend.');
      return;
    }
    setIsSyncing(true);
    setSyncProgress({ current: 0, total: queue.length });

    try {
      const res = await offlineStorage.syncAllPending((current, total) => {
        setSyncProgress({ current, total });
      });
      alert(`Sync Complete: ${res.success} synchronized, ${res.failed} failed.`);
      reloadQueue();
      onRefreshStats();
    } catch (err: any) {
      alert(`Sync Error: ${err.message}`);
    } finally {
      setIsSyncing(false);
      setSyncProgress(null);
    }
  };

  const handleClearSynced = () => {
    offlineStorage.clearSynced();
    reloadQueue();
  };

  const pendingCount = queue.filter(t => t.status === 'SAVED_LOCALLY' || t.status === 'FAILED').length;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Title & Connection Status */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Field Offline Storage & Sync Center</h1>
              <span className={`badge ${isOffline ? 'badge-inconclusive' : 'badge-verified'}`}>
                {isOffline ? 'Simulated Field Disconnect' : 'Online Connected'}
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Stores provisional field tests locally when internet is unavailable and syncs with idempotency keys upon reconnecting.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={() => setIsOffline(!isOffline)}
              className="btn btn-secondary btn-sm"
              style={{
                borderColor: isOffline ? '#EF4444' : 'rgba(255,255,255,0.12)',
                color: isOffline ? '#FCA5A5' : 'var(--text-main)'
              }}
            >
              {isOffline ? <WifiOff size={14} /> : <Wifi size={14} />}
              {isOffline ? 'Disable Offline Mode' : 'Simulate Offline Mode'}
            </button>
            
            <button
              onClick={handleSyncAll}
              className="btn btn-primary btn-sm"
              disabled={isSyncing || pendingCount === 0 || isOffline}
            >
              {isSyncing ? <RefreshCw className="animate-spin" size={14} /> : <RefreshCw size={14} />}
              Sync Pending Records ({pendingCount})
            </button>
          </div>
        </div>
      </div>

      {/* Progress banner if syncing */}
      {syncProgress && (
        <div style={{
          padding: 16,
          background: 'rgba(59, 130, 246, 0.15)',
          border: '1px solid #3B82F6',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.85rem'
        }}>
          <b>Synchronizing:</b> Processing record {syncProgress.current} of {syncProgress.total}...
        </div>
      )}

      {/* Queue Table */}
      <div className="forensic-card" style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Locally Cached Test Records</h2>
          {queue.some(t => t.status === 'SYNCHRONIZED') && (
            <button onClick={handleClearSynced} className="btn btn-secondary btn-sm">
              <Trash2 size={13} /> Clear Synced Records
            </button>
          )}
        </div>

        {queue.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '50px 0', color: 'var(--text-dim)' }}>
            <p style={{ fontWeight: 600 }}>No offline records in queue</p>
            <p style={{ fontSize: '0.8rem', marginTop: 4 }}>
              Toggle 'Simulate Offline Mode' and run a field test to test offline queuing.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="forensic-table">
              <thead>
                <tr>
                  <th>Client UUID</th>
                  <th>Test Kit</th>
                  <th>Case Ref</th>
                  <th>Status</th>
                  <th>Server Test ID</th>
                  <th>Local Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((item) => (
                  <tr key={item.client_uuid}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{item.client_uuid}</td>
                    <td>{item.kit_name}</td>
                    <td>{item.case_reference || 'N/A'}</td>
                    <td>
                      <span className={`badge ${
                        item.status === 'SYNCHRONIZED' ? 'badge-verified' :
                        item.status === 'FAILED' ? 'badge-tampered' : 'badge-inconclusive'
                      }`}>
                        {item.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      {item.server_test_id ? (
                        <button
                          onClick={() => onSelectTest(item.server_test_id!)}
                          className="btn btn-secondary btn-sm"
                          style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', padding: '2px 8px' }}
                        >
                          {item.server_test_id} <ArrowRight size={11} />
                        </button>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Pending Sync</span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
