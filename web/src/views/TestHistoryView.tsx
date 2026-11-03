import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, X, FileText, CheckCircle2, AlertOctagon, 
  HelpCircle, ShieldCheck, AlertTriangle, RefreshCw, Eye, ArrowUpDown
} from 'lucide-react';
import { TestRecordSummary, TestKit } from '../types';
import { api } from '../services/api';

interface TestHistoryViewProps {
  kits: TestKit[];
  onSelectTest: (testId: string) => void;
}

export const TestHistoryView: React.FC<TestHistoryViewProps> = ({
  kits,
  onSelectTest
}) => {
  const [tests, setTests] = useState<TestRecordSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClassification, setSelectedClassification] = useState('ALL');
  const [selectedKitId, setSelectedKitId] = useState<number | ''>('');
  const [selectedVerification, setSelectedVerification] = useState('ALL');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  const fetchRecords = async () => {
    setIsLoading(true);
    try {
      const records = await api.getTests({
        q: searchQuery || undefined,
        classification: selectedClassification !== 'ALL' ? selectedClassification : undefined,
        kit_id: selectedKitId ? Number(selectedKitId) : undefined,
        verification_status: selectedVerification !== 'ALL' ? selectedVerification : undefined
      });
      setTests(records);
    } catch (err) {
      console.error('Failed to load test history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [selectedClassification, selectedKitId, selectedVerification]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRecords();
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedClassification('ALL');
    setSelectedKitId('');
    setSelectedVerification('ALL');
  };

  const sortedTests = [...tests].sort((a, b) => {
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();
    return sortOrder === 'desc' ? timeB - timeA : timeA - timeB;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Title & Filter Bar */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Searchable Forensic Test History</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Full chain-of-custody test repository with cryptographic integrity indicators.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              className="btn btn-secondary btn-sm"
              title="Toggle chronological sorting"
            >
              <ArrowUpDown size={14} /> Date ({sortOrder === 'desc' ? 'Newest' : 'Oldest'})
            </button>
            <button onClick={fetchRecords} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>

        {/* Filter Controls Grid */}
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {/* Free Search */}
            <div style={{ flex: 1, minWidth: 260, position: 'relative' }}>
              <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 13 }} />
              <input
                type="text"
                className="forensic-input"
                style={{ paddingLeft: 38 }}
                placeholder="Search Test ID, Case Ref, Officer Name, Lot..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Classification Filter */}
            <select
              className="forensic-select"
              style={{ width: 'auto', minWidth: 170 }}
              value={selectedClassification}
              onChange={(e) => setSelectedClassification(e.target.value)}
            >
              <option value="ALL">All Outcomes</option>
              <option value="PRESUMPTIVE_POSITIVE">Presumptive Positive</option>
              <option value="PRESUMPTIVE_NEGATIVE">Presumptive Negative</option>
              <option value="INCONCLUSIVE">Inconclusive</option>
              <option value="UNABLE_TO_CLASSIFY">Unable to Classify</option>
            </select>

            {/* Kit Filter */}
            <select
              className="forensic-select"
              style={{ width: 'auto', minWidth: 180 }}
              value={selectedKitId}
              onChange={(e) => setSelectedKitId(e.target.value ? Number(e.target.value) : '')}
            >
              <option value="">All Test Kits</option>
              {kits.map((k) => (
                <option key={k.id} value={k.id}>{k.name}</option>
              ))}
            </select>

            {/* Verification Status */}
            <select
              className="forensic-select"
              style={{ width: 'auto', minWidth: 160 }}
              value={selectedVerification}
              onChange={(e) => setSelectedVerification(e.target.value)}
            >
              <option value="ALL">All Integrity States</option>
              <option value="VERIFIED">Verified</option>
              <option value="INTEGRITY_FAILED">Tampered / Failed</option>
              <option value="PENDING">Pending</option>
            </select>

            <button type="submit" className="btn btn-primary btn-sm">
              <Search size={14} /> Search
            </button>

            {(searchQuery || selectedClassification !== 'ALL' || selectedKitId !== '' || selectedVerification !== 'ALL') && (
              <button type="button" onClick={clearFilters} className="btn btn-secondary btn-sm" title="Clear all filters">
                <X size={14} /> Clear
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Results Table */}
      <div className="forensic-card" style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Showing <b>{sortedTests.length}</b> verified forensic records
          </span>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <RefreshCw className="animate-spin" size={32} style={{ margin: '0 auto 12px', display: 'block' }} />
            <p>Querying evidence database...</p>
          </div>
        ) : sortedTests.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-dim)' }}>
            <p style={{ fontSize: '1.05rem', fontWeight: 600 }}>No test records found</p>
            <p style={{ fontSize: '0.82rem', marginTop: 4 }}>Try clearing or adjusting search filters.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="forensic-table">
              <thead>
                <tr>
                  <th>Test ID</th>
                  <th>Case Ref</th>
                  <th>Kit & Analyte</th>
                  <th>Operator</th>
                  <th>Outcome</th>
                  <th>Integrity</th>
                  <th>GPS</th>
                  <th>Timestamp</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedTests.map((r) => (
                  <tr key={r.test_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                      <span
                        onClick={() => onSelectTest(r.test_id)}
                        style={{ color: '#60A5FA', cursor: 'pointer', textDecoration: 'underline' }}
                      >
                        {r.test_id}
                      </span>
                    </td>
                    <td>{r.case_reference || 'N/A'}</td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{r.kit_name}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {r.analyte_detected || r.kit_batch_number}
                      </div>
                    </td>
                    <td>
                      <div>{r.operator_name}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {r.operator_badge || 'ID-00'}
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${
                        r.classification_result === 'PRESUMPTIVE_POSITIVE' ? 'badge-positive' :
                        r.classification_result === 'PRESUMPTIVE_NEGATIVE' ? 'badge-negative' :
                        r.classification_result === 'INCONCLUSIVE' ? 'badge-inconclusive' : 'badge-unable'
                      }`}>
                        {r.classification_result.replace('PRESUMPTIVE_', '')}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        r.verification_status === 'VERIFIED' ? 'badge-verified' :
                        r.verification_status === 'INTEGRITY_FAILED' ? 'badge-tampered' : 'badge-unable'
                      }`}>
                        {r.verification_status}
                      </span>
                    </td>
                    <td>
                      {r.has_gps ? (
                        <span style={{ color: '#34D399', fontSize: '0.75rem', fontWeight: 600 }}>Active</span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>No GPS</span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                      {new Date(r.created_at).toLocaleDateString()} {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          onClick={() => onSelectTest(r.test_id)}
                          className="btn btn-secondary btn-sm"
                          title="View evidence dossier"
                        >
                          <Eye size={13} /> View
                        </button>

                        <a
                          href={api.getReportDownloadUrl(r.test_id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-secondary btn-sm"
                          title="Download PDF"
                        >
                          <FileText size={13} />
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
    </div>
  );
};
