import React, { useState } from 'react';
import { Sliders, PlusCircle, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';
import { TestKit } from '../types';
import { api } from '../services/api';

interface KitManagementViewProps {
  kits: TestKit[];
  onRefreshKits: () => void;
}

export const KitManagementView: React.FC<KitManagementViewProps> = ({ kits, onRefreshKits }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [kitName, setKitName] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [modelNumber, setModelNumber] = useState('');
  const [analyte, setAnalyte] = useState('');
  const [reactionTime, setReactionTime] = useState(60);
  const [instructions, setInstructions] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreateKit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!kitName || !manufacturer || !analyte) return;

    setIsSubmitting(true);
    try {
      await api.createKit({
        name: kitName,
        manufacturer,
        model_number: modelNumber || 'MOD-01',
        analyte,
        reaction_time_seconds: reactionTime,
        instructions
      });
      setShowAddModal(false);
      setKitName('');
      setManufacturer('');
      setModelNumber('');
      setAnalyte('');
      onRefreshKits();
    } catch (err: any) {
      alert(`Failed to create kit: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="forensic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Test Kit & Calibration Profile Management</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Administer validated colorimetric reagent kits, CIELAB reference profiles, and decision thresholds.
            </p>
          </div>

          <button onClick={() => setShowAddModal(true)} className="btn btn-primary btn-sm">
            <PlusCircle size={15} /> Add Test Kit
          </button>
        </div>
      </div>

      {/* Kit Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 16 }}>
        {kits.map((kit) => {
          const profile = kit.profiles?.[0];
          const isSim = profile?.validation_status === 'SIMULATION_ONLY';
          return (
            <div key={kit.id} className="forensic-card" style={{ padding: 24, display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{kit.name}</h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {kit.manufacturer} • Model: {kit.model_number}
                  </div>
                </div>

                <span className={`badge ${isSim ? 'badge-inconclusive' : 'badge-verified'}`}>
                  {profile?.validation_status || 'APPROVED'}
                </span>
              </div>

              <div style={{ fontSize: '0.85rem', marginBottom: 12 }}>
                <b>Target Analyte:</b> <span style={{ color: '#60A5FA' }}>{kit.analyte}</span>
              </div>

              {kit.instructions && (
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 16, lineHeight: 1.4 }}>
                  {kit.instructions}
                </p>
              )}

              {/* Profile Details */}
              {profile ? (
                <div style={{
                  marginTop: 'auto',
                  padding: 14,
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4
                }}>
                  <div><b>Profile Version:</b> {profile.profile_version}</div>
                  <div><b>Pos Reference CIELAB:</b> L*={profile.positive_cielab_l}, a*={profile.positive_cielab_a}, b*={profile.positive_cielab_b}</div>
                  <div><b>Threshold (ΔE₀₀):</b> Pos &le; {profile.positive_delta_e_threshold} | Neg &le; {profile.negative_delta_e_threshold}</div>
                  <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}><b>Source:</b> {profile.reference_source}</div>
                </div>
              ) : (
                <div style={{ marginTop: 'auto', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  No calibration profile assigned.
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add Kit Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: 28, maxWidth: 540 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: 16 }}>Configure New Field Test Kit</h2>
            
            <form onSubmit={handleCreateKit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label className="forensic-label">Kit Name</label>
                <input
                  type="text"
                  required
                  className="forensic-input"
                  placeholder="e.g. Mecke Reagent Test Kit"
                  value={kitName}
                  onChange={(e) => setKitName(e.target.value)}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label className="forensic-label">Manufacturer</label>
                  <input
                    type="text"
                    required
                    className="forensic-input"
                    placeholder="e.g. ForensicTech Labs"
                    value={manufacturer}
                    onChange={(e) => setManufacturer(e.target.value)}
                  />
                </div>

                <div>
                  <label className="forensic-label">Model Number</label>
                  <input
                    type="text"
                    className="forensic-input"
                    placeholder="e.g. MK-OPI-500"
                    value={modelNumber}
                    onChange={(e) => setModelNumber(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="forensic-label">Target Analyte</label>
                <input
                  type="text"
                  required
                  className="forensic-input"
                  placeholder="e.g. Heroin / Morphine"
                  value={analyte}
                  onChange={(e) => setAnalyte(e.target.value)}
                />
              </div>

              <div>
                <label className="forensic-label">Testing Procedure Instructions</label>
                <textarea
                  className="forensic-textarea"
                  rows={3}
                  placeholder="Testing procedure steps..."
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  Save Test Kit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
