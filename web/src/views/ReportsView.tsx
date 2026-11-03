import React, { useState, useEffect } from 'react';
import { FileText, Download, RefreshCw, Search, Clock, ShieldCheck, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export const ReportsView: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const data = await api.getReports();
      setReports(data);
    } catch (err: any) {
      // Reports list endpoint may not exist on all backend versions
      setErrorMessage(err.message || 'Failed to load reports.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const filteredReports = reports.filter(r => {
    const q = searchQuery.toLowerCase();
    return !q || r.test_id.toLowerCase().includes(q) || r.report_id.toLowerCase().includes(q);
  });

  const generateReport = async (testId: string) => {
    try {
      const res = await api.generateReport(testId);
      setSuccessMessage(`Report generated for ${testId}.`);
      fetchReports();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to generate report.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Evidence Reports</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Generate and download official forensic PDF evidence reports with QR verification codes.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={fetchReports} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
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

      {/* Report Generation Quick Start */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
          <ShieldCheck size={24} color="#06B6D4" style={{ flexShrink: 0 }} />
          <div>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 6 }}>Generate a New Report</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>
              Select a test from Test History to generate its official PDF evidence report.
              Each report includes SHA-256 hash, Ed25519 signature, and QR verification code.
            </p>
          </div>
        </div>
      </div>

      {/* Reports List */}
      <div className="forensic-card" style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Generated Evidence Reports</h2>
          <div style={{ flex: 1, minWidth: 260, position: 'relative' }}>
            <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 13 }} />
            <input
              type="text"
              className="forensic-input"
              style={{ paddingLeft: 38 }}
              placeholder="Search by Test ID or Report ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <RefreshCw className="animate-spin" size={32} style={{ margin: '0 auto 12px', display: 'block' }} />
            <p>Loading evidence reports...</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
            <p style={{ fontSize: '1.05rem', fontWeight: 600 }}>No generated reports found.</p>
            <p style={{ fontSize: '0.8rem', marginTop: 4 }}>
              Go to Test History, select a test, and download its PDF report.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="forensic-table">
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Test ID</th>
                  <th>File Size</th>
                  <th>Generated At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((r) => (
                  <tr key={r.report_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{r.report_id}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.test_id}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{(r.file_size / 1024).toFixed(1)} KB</td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <a
                          href={r.download_url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 4 }}
                        >
                          <Download size={12} /> Download PDF
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Report Contents Notice */}
      <div className="forensic-card" style={{ padding: 20 }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Report Contents
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10, fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          <div><Clock size={14} style={{ marginRight: 6 }} /> Device & Server Timestamps</div>
          <div><ShieldCheck size={14} style={{ marginRight: 6 }} /> SHA-256 Image Hash</div>
          <div><AlertTriangle size={14} style={{ marginRight: 6 }} /> Presumptive Result Disclaimer</div>
          <div><FileText size={14} style={{ marginRight: 6 }} /> QR Code for Verification</div>
        </div>
      </div>
    </div>
  );
};