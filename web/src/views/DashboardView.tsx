import React from 'react';
import { 
  CheckCircle2, AlertOctagon, HelpCircle, XCircle, 
  ShieldCheck, AlertTriangle, RefreshCw, PlusCircle, 
  ArrowRight, Activity, Calendar, Award
} from 'lucide-react';
import { DashboardStats, TestRecordSummary } from '../types';

interface DashboardViewProps {
  stats: DashboardStats | null;
  isLoading: boolean;
  onNavigate: (tab: string) => void;
  onSelectTest: (testId: string) => void;
  onRefresh: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  stats,
  isLoading,
  onNavigate,
  onSelectTest,
  onRefresh
}) => {
  if (isLoading && !stats) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--text-muted)' }}>
        <RefreshCw className="animate-spin" size={36} style={{ margin: '0 auto 16px', display: 'block' }} />
        <p>Loading forensic evidence statistics...</p>
      </div>
    );
  }

  const s = stats || {
    total_tests: 0,
    positive_count: 0,
    negative_count: 0,
    inconclusive_count: 0,
    unable_to_classify_count: 0,
    pending_sync_count: 0,
    verified_count: 0,
    integrity_failure_count: 0,
    recent_tests: [],
    kit_breakdown: [],
    monthly_trends: [],
    officer_stats: []
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Top Welcome / Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16
      }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
            Forensic Field Intelligence & Evidence Overview
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Real-time biometric and colorimetric testing analytics across all active jurisdictions.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={onRefresh} className="btn btn-secondary btn-sm" title="Refresh metrics">
            <RefreshCw size={14} /> Refresh
          </button>
          <button onClick={() => onNavigate('capture')} className="btn btn-primary btn-sm">
            <PlusCircle size={15} /> New Field Test
          </button>
        </div>
      </div>

      {/* Primary KPI Metric Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: 16
      }}>
        {/* Total Tests */}
        <div className="forensic-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span className="forensic-label">Total Conducted</span>
              <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: 4 }}>{s.total_tests}</div>
            </div>
            <div style={{ background: 'rgba(59, 130, 246, 0.15)', padding: 10, borderRadius: 10 }}>
              <Activity size={22} color="#60A5FA" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
            Cryptographically sealed records
          </div>
        </div>

        {/* Presumptive Positive */}
        <div className="forensic-card" style={{ padding: 20, borderColor: 'rgba(239, 68, 68, 0.25)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span className="forensic-label" style={{ color: '#F87171' }}>Presumptive Positive</span>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#F87171', marginTop: 4 }}>
                {s.positive_count}
              </div>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: 10, borderRadius: 10 }}>
              <AlertOctagon size={22} color="#F87171" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
            Lab confirmation required
          </div>
        </div>

        {/* Presumptive Negative */}
        <div className="forensic-card" style={{ padding: 20, borderColor: 'rgba(16, 185, 129, 0.25)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span className="forensic-label" style={{ color: '#34D399' }}>Presumptive Negative</span>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#34D399', marginTop: 4 }}>
                {s.negative_count}
              </div>
            </div>
            <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: 10, borderRadius: 10 }}>
              <CheckCircle2 size={22} color="#34D399" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
            No target analyte reaction
          </div>
        </div>

        {/* Inconclusive */}
        <div className="forensic-card" style={{ padding: 20, borderColor: 'rgba(245, 158, 11, 0.25)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span className="forensic-label" style={{ color: '#FBBF24' }}>Inconclusive</span>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FBBF24', marginTop: 4 }}>
                {s.inconclusive_count}
              </div>
            </div>
            <div style={{ background: 'rgba(245, 158, 11, 0.15)', padding: 10, borderRadius: 10 }}>
              <HelpCircle size={22} color="#FBBF24" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
            Chemical ambiguity threshold
          </div>
        </div>

        {/* Cryptographically Verified */}
        <div className="forensic-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span className="forensic-label">Integrity Verified</span>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#38BDF8', marginTop: 4 }}>
                {s.verified_count}
              </div>
            </div>
            <div style={{ background: 'rgba(56, 189, 248, 0.15)', padding: 10, borderRadius: 10 }}>
              <ShieldCheck size={22} color="#38BDF8" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
            SHA-256 & Ed25519 valid
          </div>
        </div>

        {/* Tamper Failures */}
        <div className="forensic-card" style={{
          padding: 20,
          borderColor: s.integrity_failure_count > 0 ? '#EF4444' : 'var(--border-subtle)',
          boxShadow: s.integrity_failure_count > 0 ? 'var(--shadow-glow-rose)' : 'none'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span className="forensic-label" style={{ color: s.integrity_failure_count > 0 ? '#EF4444' : undefined }}>
                Integrity Failures
              </span>
              <div style={{
                fontSize: '2rem',
                fontWeight: 800,
                color: s.integrity_failure_count > 0 ? '#EF4444' : 'var(--text-dim)',
                marginTop: 4
              }}>
                {s.integrity_failure_count}
              </div>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: 10, borderRadius: 10 }}>
              <AlertTriangle size={22} color={s.integrity_failure_count > 0 ? '#EF4444' : '#6B7280'} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>
            {s.integrity_failure_count > 0 ? 'CRITICAL TAMPER ALERT DETECTED' : 'Zero violations reported'}
          </div>
        </div>
      </div>

      {/* Visual Analytics Charts Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
        gap: 20
      }}>
        {/* Kit Breakdown Card */}
        <div className="forensic-card" style={{ padding: 24 }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 16 }}>
            Test Kit Usage Distribution
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {s.kit_breakdown.map((kb, idx) => {
              const pct = s.total_tests > 0 ? Math.round((kb.count / s.total_tests) * 100) : 0;
              const barColors = ['#3B82F6', '#06B6D4', '#8B5CF6', '#10B981', '#F59E0B'];
              const color = barColors[idx % barColors.length];
              return (
                <div key={kb.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600 }}>{kb.name}</span>
                    <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {kb.count} ({pct}%)
                    </span>
                  </div>
                  <div style={{
                    height: 8,
                    background: 'rgba(255, 255, 255, 0.08)',
                    borderRadius: 4,
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${pct}%`,
                      height: '100%',
                      background: color,
                      borderRadius: 4,
                      transition: 'width 0.4s ease'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Testing Timeline Trend */}
        <div className="forensic-card" style={{ padding: 24 }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 16 }}>
            Testing Activity Timeline
          </h2>
          <div style={{ height: 180, display: 'flex', alignItems: 'flex-end', gap: 20, paddingTop: 20 }}>
            {s.monthly_trends.map((m) => {
              const maxCount = Math.max(...s.monthly_trends.map(t => t.count), 1);
              const heightPct = Math.round((m.count / maxCount) * 100);
              return (
                <div key={m.month} style={{ flex: 1, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                  <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', marginBottom: 6 }}>
                    {m.count}
                  </div>
                  <div style={{
                    width: '100%',
                    maxWidth: 48,
                    height: `${Math.max(heightPct, 12)}%`,
                    background: 'linear-gradient(180deg, #3B82F6 0%, #1D4ED8 100%)',
                    borderRadius: '6px 6px 0 0',
                    boxShadow: '0 0 10px rgba(59, 130, 246, 0.3)'
                  }} />
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 8, fontFamily: 'var(--font-mono)' }}>
                    {m.month}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Tests Table */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Recently Conducted Field Tests</h2>
          <button onClick={() => onNavigate('history')} className="btn btn-secondary btn-sm">
            View All Tests <ArrowRight size={14} />
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="forensic-table">
            <thead>
              <tr>
                <th>Test ID</th>
                <th>Kit & Batch</th>
                <th>Operator</th>
                <th>Result</th>
                <th>Verification</th>
                <th>Captured Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {s.recent_tests.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-dim)' }}>
                    No field test records available. Create your first test using Field Capture.
                  </td>
                </tr>
              ) : (
                s.recent_tests.map((t) => (
                  <tr key={t.test_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{t.test_id}</td>
                    <td>
                      <div>{t.kit_name}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {t.kit_batch_number}
                      </div>
                    </td>
                    <td>{t.operator_name}</td>
                    <td>
                      <span className={`badge ${
                        t.classification_result === 'PRESUMPTIVE_POSITIVE' ? 'badge-positive' :
                        t.classification_result === 'PRESUMPTIVE_NEGATIVE' ? 'badge-negative' :
                        t.classification_result === 'INCONCLUSIVE' ? 'badge-inconclusive' : 'badge-unable'
                      }`}>
                        {t.classification_result.replace('PRESUMPTIVE_', '')}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        t.verification_status === 'VERIFIED' ? 'badge-verified' :
                        t.verification_status === 'INTEGRITY_FAILED' ? 'badge-tampered' : 'badge-unable'
                      }`}>
                        {t.verification_status}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-dim)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                      {new Date(t.created_at).toLocaleDateString()} {new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td>
                      <button
                        onClick={() => onSelectTest(t.test_id)}
                        className="btn btn-secondary btn-sm"
                      >
                        Inspect Evidence
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
