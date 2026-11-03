import React, { useState, useEffect } from 'react';
import { History, Shield, RefreshCw, Link2, CheckCircle2 } from 'lucide-react';
import { AuditLogItem } from '../types';
import { api } from '../services/api';

export const AuditLogsView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const data = await api.getAuditLogs(100);
      setLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Title */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
                Chain of Custody & Security Audit Trail
              </h1>
              <span className="badge badge-verified">
                <Link2 size={12} /> HASH-LINKED CHAIN
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Immutable sequence where each event cryptographically references the SHA-256 hash of the preceding event.
            </p>
          </div>

          <button onClick={fetchLogs} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} /> Refresh Logs
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="forensic-card" style={{ padding: 20 }}>
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <RefreshCw className="animate-spin" size={32} style={{ margin: '0 auto 12px', display: 'block' }} />
            <p>Querying immutable audit chain...</p>
          </div>
        ) : logs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
            No audit events recorded yet.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="forensic-table">
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Action / Event Type</th>
                  <th>Operator</th>
                  <th>Target Record</th>
                  <th>Cryptographic Event Hash</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const isTamper = log.event_type.includes('TAMPER');
                  const isVerify = log.event_type.includes('VERIF');
                  const isSign = log.event_type.includes('SIGN');

                  return (
                    <tr key={log.id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                        {log.event_id}
                      </td>
                      <td>
                        <span className={`badge ${
                          isTamper ? 'badge-tampered' :
                          isVerify ? 'badge-verified' :
                          isSign ? 'badge-positive' : 'badge-unable'
                        }`}>
                          {log.event_type}
                        </span>
                      </td>
                      <td>{log.user_name || 'System / Batch'}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#60A5FA' }}>
                        {log.related_record_id || '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                        <span title={`Previous Hash: ${log.prev_event_hash}`}>
                          {log.event_hash ? `${log.event_hash.substring(0, 16)}...` : 'N/A'}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
