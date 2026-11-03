import React, { useState, useEffect } from 'react';
import { 
  X, ShieldCheck, AlertTriangle, FileText, CheckCircle2, AlertOctagon, 
  HelpCircle, RefreshCw, Copy, Check, MapPin, Clock, Camera, Sparkles, Bug
} from 'lucide-react';
import { TestRecordDetail } from '../types';
import { api } from '../services/api';

interface TestDetailModalProps {
  testId: string;
  onClose: () => void;
  onRefreshList?: () => void;
}

export const TestDetailModal: React.FC<TestDetailModalProps> = ({
  testId,
  onClose,
  onRefreshList
}) => {
  const [record, setRecord] = useState<TestRecordDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isTampering, setIsTampering] = useState(false);
  const [verificationFeedback, setVerificationFeedback] = useState<any | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  const fetchDetail = async () => {
    setIsLoading(true);
    try {
      const data = await api.getTestDetail(testId);
      setRecord(data);
    } catch (err) {
      console.error('Failed to load test detail:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [testId]);

  const handleVerify = async () => {
    setIsVerifying(true);
    try {
      const res = await api.verifyEvidence(testId);
      setVerificationFeedback(res);
      await fetchDetail();
      if (onRefreshList) onRefreshList();
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSimulateTampering = async () => {
    if (!window.confirm('This will modify 16 bytes of the original stored image to demonstrate tamper detection. Proceed?')) {
      return;
    }
    setIsTampering(true);
    try {
      await api.simulateTampering(testId);
      // Immediately run verification to show the failure
      const res = await api.verifyEvidence(testId);
      setVerificationFeedback(res);
      await fetchDetail();
      if (onRefreshList) onRefreshList();
    } catch (err: any) {
      alert(`Tamper simulation error: ${err.message}`);
    } finally {
      setIsTampering(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  if (isLoading || !record) {
    return (
      <div className="modal-overlay">
        <div className="modal-content" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw className="animate-spin" size={32} style={{ margin: '0 auto 12px' }} />
          <p>Retrieving sealed forensic dossier...</p>
        </div>
      </div>
    );
  }

  const backendHost = 'http://localhost:8000';
  const origImgUrl = record.original_image_url ? `${backendHost}${record.original_image_url}` : null;
  const procImgUrl = record.processed_image_url ? `${backendHost}${record.processed_image_url}` : null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: 28 }}>
        {/* Header Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Forensic Evidence Dossier</h2>
              <span className={`badge ${
                record.verification_status === 'VERIFIED' ? 'badge-verified' :
                record.verification_status === 'INTEGRITY_FAILED' ? 'badge-tampered' : 'badge-unable'
              }`}>
                {record.verification_status}
              </span>
            </div>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              ID: {record.test_id} • Case: {record.case_reference || 'N/A'} • Key: {record.signing_key_id}
            </p>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <a
              href={api.getReportDownloadUrl(record.test_id)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary btn-sm"
            >
              <FileText size={14} /> PDF Report
            </a>
            <button onClick={onClose} className="btn btn-secondary btn-sm">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Presumptive Result Banner */}
        <div style={{
          padding: 18,
          borderRadius: 'var(--radius-md)',
          background: record.classification_result === 'PRESUMPTIVE_POSITIVE' ? 'rgba(239, 68, 68, 0.12)' :
                      record.classification_result === 'PRESUMPTIVE_NEGATIVE' ? 'rgba(16, 185, 129, 0.12)' :
                      record.classification_result === 'INCONCLUSIVE' ? 'rgba(245, 158, 11, 0.12)' : 'rgba(107, 114, 128, 0.12)',
          border: `1.5px solid ${
            record.classification_result === 'PRESUMPTIVE_POSITIVE' ? '#EF4444' :
            record.classification_result === 'PRESUMPTIVE_NEGATIVE' ? '#10B981' :
            record.classification_result === 'INCONCLUSIVE' ? '#F59E0B' : '#6B7280'
          }`,
          marginBottom: 20
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {record.classification_result === 'PRESUMPTIVE_POSITIVE' ? <AlertOctagon size={28} color="#EF4444" /> :
               record.classification_result === 'PRESUMPTIVE_NEGATIVE' ? <CheckCircle2 size={28} color="#10B981" /> :
               record.classification_result === 'INCONCLUSIVE' ? <HelpCircle size={28} color="#F59E0B" /> : <AlertTriangle size={28} color="#6B7280" />}
              <div>
                <div style={{ fontSize: '1.2rem', fontWeight: 900 }}>
                  {record.classification_result.replace('_', ' ')}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-main)' }}>
                  <b>Analyte:</b> {record.analyte_detected || 'None Identified'} • <b>Reason:</b> {record.classification_reason || 'N/A'}
                </div>
              </div>
            </div>

            <span className="badge badge-unable" style={{ fontFamily: 'var(--font-mono)' }}>
              Confidence: {Math.round((record.classification_confidence || 0) * 100)}%
            </span>
          </div>
        </div>

        {/* Dual Photographic Evidence Inspection (Original vs Calibrated) */}
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: 10 }}>
            Photometric Evidence Comparison
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
            {/* Original Image */}
            <div style={{ background: '#000', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
              <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.06)', fontSize: '0.75rem', fontWeight: 700, display: 'flex', justifyContent: 'space-between' }}>
                <span>ORIGINAL CAPTURE (Immutable Raw Bytes)</span>
                <span style={{ color: 'var(--text-dim)' }}>SHA-256 SEALED</span>
              </div>
              {origImgUrl ? (
                <img src={origImgUrl} alt="Original evidence" style={{ width: '100%', height: 260, objectFit: 'contain' }} />
              ) : (
                <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>Image missing</div>
              )}
            </div>

            {/* Calibrated Derivative */}
            <div style={{ background: '#000', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
              <div style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.06)', fontSize: '0.75rem', fontWeight: 700, display: 'flex', justifyContent: 'space-between' }}>
                <span>CALIBRATED DERIVATIVE (CIELAB & ROI Overlay)</span>
                <span style={{ color: '#06B6D4' }}>ΔE₀₀ CALIBRATED</span>
              </div>
              {procImgUrl ? (
                <img src={procImgUrl} alt="Processed analysis" style={{ width: '100%', height: 260, objectFit: 'contain' }} />
              ) : (
                <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>Derivative missing</div>
              )}
            </div>
          </div>
        </div>

        {/* Colorimetry & Telemetry Breakdown */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: 16,
          marginBottom: 20
        }}>
          {/* Reaction Colorimetry */}
          <div style={{ background: 'rgba(17, 24, 39, 0.7)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <span className="forensic-label">Measured CIELAB & Distances</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
              <div style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                background: record.analysis?.reaction_hex || '#1478C3',
                border: '2px solid rgba(255,255,255,0.3)'
              }} />
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                  {record.analysis?.reaction_cielab ? `L*=${record.analysis.reaction_cielab.L} a*=${record.analysis.reaction_cielab.a} b*=${record.analysis.reaction_cielab.b}` : 'N/A'}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 2 }}>
                  dE(Pos): <b>{record.analysis?.positive_delta_e?.toFixed(1) || 'N/A'}</b> | dE(Neg): <b>{record.analysis?.negative_delta_e?.toFixed(1) || 'N/A'}</b>
                </div>
              </div>
            </div>
          </div>

          {/* Location & GPS */}
          <div style={{ background: 'rgba(17, 24, 39, 0.7)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <span className="forensic-label">GPS Telemetry</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
              <MapPin size={20} color="#34D399" />
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                  {record.gps_latitude ? `${record.gps_latitude.toFixed(5)}, ${record.gps_longitude?.toFixed(5)}` : 'Location Unavailable'}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                  {record.gps_accuracy_meters ? `Accuracy: ±${record.gps_accuracy_meters.toFixed(1)}m` : record.location_unavailable_reason || 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Timestamps */}
          <div style={{ background: 'rgba(17, 24, 39, 0.7)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <span className="forensic-label">Dual Provenance Timestamps</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
              <Clock size={20} color="#60A5FA" />
              <div>
                <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                  <b>Device:</b> {new Date(record.device_timestamp).toLocaleString()}
                </div>
                <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                  <b>Server:</b> {new Date(record.server_timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Cryptographic Verification Terminal */}
        <div style={{
          background: '#090D16',
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          padding: 20,
          marginBottom: 20
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShieldCheck size={18} color="#38BDF8" />
              <span style={{ fontSize: '0.9rem', fontWeight: 800, letterSpacing: '0.04em' }}>
                CRYPTOGRAPHIC VERIFICATION TERMINAL
              </span>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={handleVerify}
                className="btn btn-primary btn-sm"
                disabled={isVerifying}
              >
                {isVerifying ? <RefreshCw className="animate-spin" size={13} /> : <ShieldCheck size={13} />}
                Verify Integrity
              </button>

              <button
                onClick={handleSimulateTampering}
                className="btn btn-danger btn-sm"
                disabled={isTampering}
                title="Inject byte modification to demonstrate tamper detection"
              >
                <Bug size={13} /> Simulate Tampering
              </button>
            </div>
          </div>

          {/* Verification Feedback Banner if just verified */}
          {verificationFeedback && (
            <div style={{
              padding: '12px 14px',
              borderRadius: 'var(--radius-sm)',
              background: verificationFeedback.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.2)',
              border: `1px solid ${verificationFeedback.status === 'VERIFIED' ? '#10B981' : '#EF4444'}`,
              marginBottom: 14,
              fontSize: '0.82rem'
            }}>
              <div style={{ fontWeight: 800, color: verificationFeedback.status === 'VERIFIED' ? '#34D399' : '#FCA5A5' }}>
                {verificationFeedback.status === 'VERIFIED' ? '✓ CRYPTOGRAPHIC VERIFICATION SUCCESSFUL' : '⚠ INTEGRITY VIOLATION DETECTED'}
              </div>
              <div style={{ color: 'var(--text-main)', marginTop: 2 }}>{verificationFeedback.details}</div>
            </div>
          )}

          {/* Hash & Signature display */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
            <div>
              <div style={{ color: 'var(--text-dim)', marginBottom: 2 }}>ORIGINAL IMAGE SHA-256 HASH</div>
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                padding: '6px 10px',
                borderRadius: 4,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                wordBreak: 'break-all'
              }}>
                <span>{record.original_image_hash || 'N/A'}</span>
                {record.original_image_hash && (
                  <button
                    onClick={() => copyToClipboard(record.original_image_hash!)}
                    style={{ background: 'none', border: 'none', color: '#60A5FA', cursor: 'pointer', marginLeft: 8 }}
                    title="Copy hash"
                  >
                    {copiedHash ? <Check size={14} /> : <Copy size={14} />}
                  </button>
                )}
              </div>
            </div>

            <div>
              <div style={{ color: 'var(--text-dim)', marginBottom: 2 }}>ED25519 ASYMMETRIC DIGITAL SIGNATURE</div>
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                padding: '6px 10px',
                borderRadius: 4,
                wordBreak: 'break-all',
                color: '#93C5FD'
              }}>
                {record.digital_signature ? `${record.digital_signature.substring(0, 72)}...` : 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {/* Legal Disclaimer */}
        <div style={{
          padding: 12,
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.78rem',
          color: '#FCA5A5',
          lineHeight: 1.4
        }}>
          <b>STATUTORY DISCLAIMER:</b> Automated output is a presumptive field-test result. It is not a laboratory-confirmed identification. Confirmatory qualitative and quantitative laboratory testing (e.g. GC-MS) remains required.
        </div>
      </div>
    </div>
  );
};
