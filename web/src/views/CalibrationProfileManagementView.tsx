import React, { useState, useEffect } from 'react';
import { TestKit, TestKitProfile } from '../types';
import { api } from '../services/api';
import { Sliders, PlusCircle, RefreshCw, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const CalibrationProfileManagementView: React.FC = () => {
  const [kits, setKits] = useState<TestKit[]>([]);
  const [selectedKitId, setSelectedKitId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newProfile, setNewProfile] = useState({
    profile_version: 'V1.0',
    validation_status: 'PENDING_VALIDATION' as const,
    reference_source: '',
    approval_details: '',
    positive_cielab_l: 0,
    positive_cielab_a: 0,
    positive_cielab_b: 0,
    positive_delta_e_threshold: 18.0,
    negative_cielab_l: 0,
    negative_cielab_a: 0,
    negative_cielab_b: 0,
    negative_delta_e_threshold: 16.0,
    inconclusive_delta_e_threshold: 8.0,
    reaction_roi_x: 0.38,
    reaction_roi_y: 0.25,
    reaction_roi_w: 0.54,
    reaction_roi_h: 0.50
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchKits = async () => {
    try {
      const data = await api.getKits();
      setKits(data);
      if (data.length > 0 && !selectedKitId) {
        setSelectedKitId(data[0].id);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load test kits.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchKits();
  }, []);

  const selectedKit = kits.find(k => k.id === selectedKitId);
  const profiles = selectedKit?.profiles || [];

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedKitId) return;

    setIsSubmitting(true);
    try {
      await api.createCalibrationProfile(selectedKitId, {
        ...newProfile,
        kit_id: selectedKitId
      });
      setShowAddModal(false);
      setSuccessMessage('Calibration profile created successfully.');
      fetchKits();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create calibration profile.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return '#10B981';
      case 'PENDING_VALIDATION': return '#F59E0B';
      case 'SIMULATION_ONLY': return '#8B5CF6';
      default: return '#6B7280';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Calibration Profile Management</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Versioned CIELAB reference profiles and decision thresholds per test kit.
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            disabled={!selectedKitId}
            className="btn btn-primary btn-sm"
          >
            <PlusCircle size={15} /> Add Profile
          </button>
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

      {/* Kit Selector */}
      <div className="forensic-card" style={{ padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          <label className="forensic-label">Select Test Kit</label>
          <select
            className="forensic-select"
            style={{ minWidth: 300 }}
            value={selectedKitId ?? ''}
            onChange={(e) => setSelectedKitId(e.target.value ? Number(e.target.value) : null)}
            disabled={isLoading}
          >
            <option value="">-- Choose a test kit --</option>
            {kits.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name} — {k.analyte}
              </option>
            ))}
          </select>
          <button onClick={fetchKits} className="btn btn-secondary btn-sm" disabled={isLoading}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {selectedKit && (
        <>
          {/* Profile Details */}
          <div className="forensic-card" style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 4 }}>
                  {selectedKit.name} — Calibration Profiles
                </h2>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {selectedKit.manufacturer} • Model: {selectedKit.model_number} • Analyte: {selectedKit.analyte}
                </div>
              </div>
              <span style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.72rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                fontFamily: 'var(--font-mono)',
                background: 'rgba(17, 24, 39, 0.6)',
                color: '#60A5FA',
                border: '1px solid #60A5FA40'
              }}>
                Kit Instructions Available
              </span>
            </div>

            {selectedKit.instructions && (
              <div style={{
                padding: '12px 16px',
                background: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                color: '#93C5FD',
                marginBottom: 20
              }}>
                <b>Testing Procedure:</b> {selectedKit.instructions}
              </div>
            )}

            {profiles.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
                <ShieldAlert size={32} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.5 }} />
                <p>No calibration profiles assigned to this kit.</p>
                <p style={{ fontSize: '0.8rem', marginTop: 4 }}>
                  Without an approved profile, automated classification is unavailable for this kit.
                </p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="forensic-table">
                  <thead>
                    <tr>
                      <th>Profile Version</th>
                      <th>Validation Status</th>
                      <th>Positive Ref (L*,a*,b*)</th>
                      <th>Neg Ref (L*,a*,b*)</th>
                      <th>Thresholds (ΔE₀₀)</th>
                      <th>ROI (x,y,w,h)</th>
                      <th>Reference Source</th>
                      <th>Approval Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profiles.map((p) => (
                      <tr key={p.id}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{p.profile_version}</td>
                        <td>
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            background: `rgba(${statusColor(p.validation_status) === '#10B981' ? '16,185,129' : statusColor(p.validation_status) === '#F59E0B' ? '245,158,11' : '139,92,246'},0.15)`,
                            color: statusColor(p.validation_status),
                            border: `1px solid ${statusColor(p.validation_status)}40`
                          }}>
                            {p.validation_status.replace('_', ' ')}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                          L*{p.positive_cielab_l.toFixed(1)} a*{p.positive_cielab_a.toFixed(1)} b*{p.positive_cielab_b.toFixed(1)}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                          L*{p.negative_cielab_l.toFixed(1)} a*{p.negative_cielab_a.toFixed(1)} b*{p.negative_cielab_b.toFixed(1)}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                          Pos ≤ {p.positive_delta_e_threshold}<br/>
                          Neg ≤ {p.negative_delta_e_threshold}<br/>
                          Ambig ≤ {p.inconclusive_delta_e_threshold}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
                          {p.reaction_roi_x.toFixed(2)}, {p.reaction_roi_y.toFixed(2)}, {p.reaction_roi_w.toFixed(2)}, {p.reaction_roi_h.toFixed(2)}
                        </td>
                        <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: 200 }}>{p.reference_source}</td>
                        <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: 200 }}>{p.approval_details || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Add Profile Modal */}
          {showAddModal && (
            <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: 28, maxWidth: 600 }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: 16 }}>
                  Create Calibration Profile for {selectedKit.name}
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 20 }}>
                  Profiles must be based on manufacturer documentation or independently validated reference data.
                  Only approved administrators may activate validated profiles.
                </p>

                <form onSubmit={handleCreateProfile} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                    <div>
                      <label className="forensic-label">Profile Version</label>
                      <input
                        type="text"
                        required
                        className="forensic-input"
                        placeholder="e.g. V1.4"
                        value={newProfile.profile_version}
                        onChange={(e) => setNewProfile({ ...newProfile, profile_version: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="forensic-label">Validation Status</label>
                      <select
                        className="forensic-select"
                        value={newProfile.validation_status}
                        onChange={(e) => setNewProfile({ ...newProfile, validation_status: e.target.value as any })}
                      >
                        <option value="PENDING_VALIDATION">Pending Validation</option>
                        <option value="APPROVED">Approved</option>
                        <option value="SIMULATION_ONLY">Simulation Only</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="forensic-label">Reference Source</label>
                    <input
                      type="text"
                      required
                      className="forensic-input"
                      placeholder="e.g. SWGDRUG Validation Protocol 2025"
                      value={newProfile.reference_source}
                      onChange={(e) => setNewProfile({ ...newProfile, reference_source: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="forensic-label">Approval Details</label>
                    <input
                      type="text"
                      className="forensic-input"
                      placeholder="e.g. Approved by FSB-2025-08"
                      value={newProfile.approval_details}
                      onChange={(e) => setNewProfile({ ...newProfile, approval_details: e.target.value })}
                    />
                  </div>

                  <div style={{ background: 'rgba(17, 24, 39, 0.4)', padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                    <h3 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Validated Positive Reference (CIELAB)
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                      <div>
                        <label className="forensic-label" style={{ fontSize: '0.7rem' }}>L*</label>
                        <input type="number" className="forensic-input" step="0.1"
                          value={newProfile.positive_cielab_l}
                          onChange={(e) => setNewProfile({ ...newProfile, positive_cielab_l: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                      <div>
                        <label className="forensic-label" style={{ fontSize: '0.7rem' }}>a*</label>
                        <input type="number" className="forensic-input" step="0.1"
                          value={newProfile.positive_cielab_a}
                          onChange={(e) => setNewProfile({ ...newProfile, positive_cielab_a: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                      <div>
                        <label className="forensic-label" style={{ fontSize: '0.7rem' }}>b*</label>
                        <input type="number" className="forensic-input" step="0.1"
                          value={newProfile.positive_cielab_b}
                          onChange={(e) => setNewProfile({ ...newProfile, positive_cielab_b: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ background: 'rgba(17, 24, 39, 0.4)', padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginTop: 10 }}>
                    <h3 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Validated Negative Reference (CIELAB)
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                      <div>
                        <label className="forensic-label" style={{ fontSize: '0.7rem' }}>L*</label>
                        <input type="number" className="forensic-input" step="0.1"
                          value={newProfile.negative_cielab_l}
                          onChange={(e) => setNewProfile({ ...newProfile, negative_cielab_l: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                      <div>
                        <label className="forensic-label" style={{ fontSize: '0.7rem' }}>a*</label>
                        <input type="number" className="forensic-input" step="0.1"
                          value={newProfile.negative_cielab_a}
                          onChange={(e) => setNewProfile({ ...newProfile, negative_cielab_a: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                      <div>
                        <label className="forensic-label" style={{ fontSize: '0.7rem' }}>b*</label>
                        <input type="number" className="forensic-input" step="0.1"
                          value={newProfile.negative_cielab_b}
                          onChange={(e) => setNewProfile({ ...newProfile, negative_cielab_b: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginTop: 10 }}>
                    <div>
                      <label className="forensic-label" style={{ fontSize: '0.7rem' }}>Pos Threshold (ΔE₀₀)</label>
                      <input type="number" className="forensic-input" step="0.1"
                        value={newProfile.positive_delta_e_threshold}
                        onChange={(e) => setNewProfile({ ...newProfile, positive_delta_e_threshold: parseFloat(e.target.value) || 18 })}
                      />
                    </div>
                    <div>
                      <label className="forensic-label" style={{ fontSize: '0.7rem' }}>Neg Threshold (ΔE₀₀)</label>
                      <input type="number" className="forensic-input" step="0.1"
                        value={newProfile.negative_delta_e_threshold}
                        onChange={(e) => setNewProfile({ ...newProfile, negative_delta_e_threshold: parseFloat(e.target.value) || 16 })}
                      />
                    </div>
                    <div>
                      <label className="forensic-label" style={{ fontSize: '0.7rem' }}>Inconclusive Margin</label>
                      <input type="number" className="forensic-input" step="0.1"
                        value={newProfile.inconclusive_delta_e_threshold}
                        onChange={(e) => setNewProfile({ ...newProfile, inconclusive_delta_e_threshold: parseFloat(e.target.value) || 8 })}
                      />
                    </div>
                    <div>
                      <label className="forensic-label" style={{ fontSize: '0.7rem' }}>ROI X</label>
                      <input type="number" className="forensic-input" step="0.01"
                        value={newProfile.reaction_roi_x}
                        onChange={(e) => setNewProfile({ ...newProfile, reaction_roi_x: parseFloat(e.target.value) || 0.38 })}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                    <div>
                      <label className="forensic-label" style={{ fontSize: '0.7rem' }}>ROI Y</label>
                      <input type="number" className="forensic-input" step="0.01"
                        value={newProfile.reaction_roi_y}
                        onChange={(e) => setNewProfile({ ...newProfile, reaction_roi_y: parseFloat(e.target.value) || 0.25 })}
                      />
                    </div>
                    <div>
                      <label className="forensic-label" style={{ fontSize: '0.7rem' }}>ROI W</label>
                      <input type="number" className="forensic-input" step="0.01"
                        value={newProfile.reaction_roi_w}
                        onChange={(e) => setNewProfile({ ...newProfile, reaction_roi_w: parseFloat(e.target.value) || 0.54 })}
                      />
                    </div>
                    <div>
                      <label className="forensic-label" style={{ fontSize: '0.7rem' }}>ROI H</label>
                      <input type="number" className="forensic-input" step="0.01"
                        value={newProfile.reaction_roi_h}
                        onChange={(e) => setNewProfile({ ...newProfile, reaction_roi_h: parseFloat(e.target.value) || 0.50 })}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                    <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary">
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                      {isSubmitting ? <RefreshCw className="animate-spin" size={14} /> : <CheckCircle2 size={14} />}
                      Save Profile
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};