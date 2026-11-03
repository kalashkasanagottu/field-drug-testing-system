import React, { useState, useEffect } from 'react';
import { ShieldCheck, Search, Key, AlertTriangle, CheckCircle2, RefreshCw, Bug, Copy, Check } from 'lucide-react';
import { api } from '../services/api';
import { TestRecordSummary } from '../types';

interface VerificationPortalViewProps {
  onSelectTest: (testId: string) => void;
}

export const VerificationPortalView: React.FC<VerificationPortalViewProps> = ({ onSelectTest }) => {
  const [testIdInput, setTestIdInput] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [publicKeyInfo, setPublicKeyInfo] = useState<any | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [recentTests, setRecentTests] = useState<TestRecordSummary[]>([]);

  useEffect(() => {
    // Load public key and recent tests
    api.getPublicKey().then(setPublicKeyInfo).catch(console.error);
    api.getTests({}).then(setRecentTests).catch(console.error);
  }, []);

  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!testIdInput) return;

    setIsVerifying(true);
    setVerificationResult(null);
    try {
      const res = await api.verifyEvidence(testIdInput.trim());
      setVerificationResult(res);
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSelectQuickTest = (testId: string) => {
    setTestIdInput(testId);
    api.verifyEvidence(testId).then(setVerificationResult).catch(console.error);
  };

  const handleSimulateTamper = async () => {
    if (!testIdInput) return;
    if (!window.confirm(`Simulate altering image bytes for ${testIdInput}?`)) return;
    try {
      await api.simulateTampering(testIdInput.trim());
      const res = await api.verifyEvidence(testIdInput.trim());
      setVerificationResult(res);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  const copyPublicKey = () => {
    if (publicKeyInfo?.public_key_hex) {
      navigator.clipboard.writeText(publicKeyInfo.public_key_hex);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Title */}
      <div className="forensic-card" style={{ padding: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShieldCheck size={26} color="#FFF" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
              Judicial Evidence & Signature Verification Station
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Independent cryptographic verification of SHA-256 raw evidence hashes and Ed25519 digital signatures.
            </p>
          </div>
        </div>

        {/* Verification Form */}
        <form onSubmit={handleVerify} style={{ display: 'flex', gap: 10, marginTop: 20 }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: 14, top: 13 }} />
            <input
              type="text"
              className="forensic-input"
              style={{ paddingLeft: 40, fontFamily: 'var(--font-mono)' }}
              placeholder="Enter Test Record ID (e.g. DT-20261102-C7E1)..."
              value={testIdInput}
              onChange={(e) => setTestIdInput(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={isVerifying || !testIdInput}>
            {isVerifying ? <RefreshCw className="animate-spin" size={15} /> : <ShieldCheck size={15} />}
            Verify Record
          </button>
        </form>

        {/* Quick select pills from database */}
        {recentTests.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, marginRight: 8 }}>
              Select Active Test ID:
            </span>
            <div style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
              {recentTests.slice(0, 5).map(t => (
                <button
                  key={t.test_id}
                  type="button"
                  onClick={() => handleSelectQuickTest(t.test_id)}
                  className="btn btn-secondary btn-sm"
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    padding: '3px 8px',
                    borderColor: testIdInput === t.test_id ? 'var(--accent-blue)' : undefined
                  }}
                >
                  {t.test_id}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Verification Terminal Result */}
      {verificationResult && (
        <div className="forensic-card" style={{
          padding: 28,
          borderColor: verificationResult.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.4)' : '#EF4444',
          boxShadow: verificationResult.status === 'VERIFIED' ? 'var(--shadow-glow-emerald)' : 'var(--shadow-glow-rose)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {verificationResult.status === 'VERIFIED' ? (
                <CheckCircle2 size={36} color="#10B981" />
              ) : (
                <AlertTriangle size={36} color="#EF4444" />
              )}
              <div>
                <div style={{
                  fontSize: '1.25rem',
                  fontWeight: 900,
                  color: verificationResult.status === 'VERIFIED' ? '#34D399' : '#F87171'
                }}>
                  {verificationResult.status === 'VERIFIED' ? 'CRYPTOGRAPHIC INTEGRITY CONFIRMED' : 'EVIDENCE INTEGRITY FAILURE DETECTED'}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: 2 }}>
                  {verificationResult.details}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => onSelectTest(verificationResult.test_id)}
                className="btn btn-secondary btn-sm"
              >
                Inspect Dossier
              </button>
              <button
                onClick={handleSimulateTamper}
                className="btn btn-danger btn-sm"
                title="Inject byte modification into evidence image"
              >
                <Bug size={13} /> Simulate Tampering
              </button>
            </div>
          </div>

          {/* Verification Breakdown Table */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 16,
            marginTop: 20
          }}>
            <div style={{ background: 'rgba(17, 24, 39, 0.7)', padding: 16, borderRadius: 'var(--radius-md)' }}>
              <span className="forensic-label">SHA-256 Image Integrity</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                <span className={`badge ${verificationResult.image_hash_verified ? 'badge-verified' : 'badge-tampered'}`}>
                  {verificationResult.image_hash_verified ? 'Match Verified' : 'Hash Mismatch'}
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', marginTop: 8, wordBreak: 'break-all' }}>
                <b>Stored:</b> {verificationResult.original_image_hash}<br/>
                <b>Recomputed:</b> {verificationResult.computed_image_hash}
              </div>
            </div>

            <div style={{ background: 'rgba(17, 24, 39, 0.7)', padding: 16, borderRadius: 'var(--radius-md)' }}>
              <span className="forensic-label">Ed25519 Signature Verification</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                <span className={`badge ${verificationResult.signature_verified ? 'badge-verified' : 'badge-tampered'}`}>
                  {verificationResult.signature_verified ? 'Signature Valid' : 'Signature Invalid'}
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', marginTop: 8 }}>
                <b>Key Identifier:</b> {verificationResult.signing_key_id}<br/>
                <b>Algorithm:</b> Ed25519 (RFC 8032)
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Public Key Display Card */}
      {publicKeyInfo && (
        <div className="forensic-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Key size={16} color="#06B6D4" />
              <h2 style={{ fontSize: '0.95rem', fontWeight: 700 }}>
                Active Public Key for Defense & Judicial Audit
              </h2>
            </div>
            <button onClick={copyPublicKey} className="btn btn-secondary btn-sm">
              {copiedKey ? <Check size={13} /> : <Copy size={13} />}
              {copiedKey ? 'Copied' : 'Copy Key'}
            </button>
          </div>

          <div style={{
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: '#93C5FD',
            wordBreak: 'break-all'
          }}>
            {publicKeyInfo.public_key_hex}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 6 }}>
            Algorithm: <b>{publicKeyInfo.algorithm}</b> | Key ID: <b>{publicKeyInfo.key_id}</b>
          </div>
        </div>
      )}
    </div>
  );
};
