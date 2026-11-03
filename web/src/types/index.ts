export type UserRole = 'ADMIN' | 'FIELD_OFFICER' | 'SUPERVISOR' | 'AUDITOR';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  badge_number?: string;
  department: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TestKitProfile {
  id: number;
  kit_id: number;
  profile_version: string;
  validation_status: 'APPROVED' | 'PENDING_VALIDATION' | 'SIMULATION_ONLY';
  reference_source: string;
  approval_details?: string;
  positive_cielab_l: number;
  positive_cielab_a: number;
  positive_cielab_b: number;
  positive_delta_e_threshold: number;
  negative_cielab_l: number;
  negative_cielab_a: number;
  negative_cielab_b: number;
  negative_delta_e_threshold: number;
  inconclusive_delta_e_threshold: number;
  reaction_roi_x: number;
  reaction_roi_y: number;
  reaction_roi_w: number;
  reaction_roi_h: number;
}

export interface TestKit {
  id: number;
  name: string;
  manufacturer: string;
  model_number: string;
  analyte: string;
  reaction_time_seconds: number;
  instructions?: string;
  is_active: boolean;
  profiles: TestKitProfile[];
}

export type ClassificationResultType = 
  | 'PRESUMPTIVE_POSITIVE' 
  | 'PRESUMPTIVE_NEGATIVE' 
  | 'INCONCLUSIVE' 
  | 'UNABLE_TO_CLASSIFY';

export type VerificationStatusType = 'VERIFIED' | 'INTEGRITY_FAILED' | 'PENDING';
export type SyncStatusType = 'SAVED_LOCALLY' | 'PENDING_SYNC' | 'SYNCHRONIZED' | 'FAILED';

export interface TestRecordSummary {
  id: number;
  test_id: string;
  case_reference?: string;
  operator_name: string;
  operator_badge?: string;
  kit_name: string;
  kit_batch_number: string;
  analyte_detected?: string;
  classification_result: ClassificationResultType;
  verification_status: VerificationStatusType;
  sync_status: SyncStatusType;
  original_image_hash?: string;
  device_timestamp: string;
  server_timestamp: string;
  has_gps: boolean;
  created_at: string;
}

export interface ImageAnalysisData {
  blur_score: number;
  is_blurry: boolean;
  illumination_score: number;
  is_underexposed: boolean;
  is_overexposed: boolean;
  card_detected: boolean;
  calibration_error_delta_e?: number;
  reaction_cielab?: {
    L: number;
    a: number;
    b: number;
  };
  reaction_hex?: string;
  positive_delta_e?: number;
  negative_delta_e?: number;
  quality_passed: boolean;
  quality_notes?: string;
}

export interface VerificationEventData {
  id: number;
  verifier_name: string;
  hash_verified: boolean;
  signature_verified: boolean;
  details: string;
  timestamp: string;
}

export interface TestRecordDetail {
  id: number;
  test_id: string;
  case_reference?: string;
  operator_id: number;
  operator_name: string;
  operator_badge?: string;
  kit_id: number;
  kit_name: string;
  kit_manufacturer: string;
  kit_batch_number: string;
  kit_expiry_date?: string;
  notes?: string;
  classification_result: ClassificationResultType;
  classification_reason?: string;
  classification_confidence?: number;
  analyte_detected?: string;
  algorithm_version: string;
  profile_version?: string;
  gps_latitude?: number;
  gps_longitude?: number;
  gps_accuracy_meters?: number;
  location_unavailable_reason?: string;
  device_timestamp: string;
  server_timestamp: string;
  original_image_url?: string;
  processed_image_url?: string;
  original_image_hash?: string;
  image_byte_size?: number;
  digital_signature?: string;
  signature_algorithm: string;
  signing_key_id?: string;
  canonical_record_hash?: string;
  verification_status: VerificationStatusType;
  is_provisional: boolean;
  client_uuid?: string;
  sync_status: SyncStatusType;
  created_at: string;
  analysis?: ImageAnalysisData;
  verifications: VerificationEventData[];
}

export interface DashboardStats {
  total_tests: number;
  positive_count: number;
  negative_count: number;
  inconclusive_count: number;
  unable_to_classify_count: number;
  pending_sync_count: number;
  verified_count: number;
  integrity_failure_count: number;
  recent_tests: TestRecordSummary[];
  kit_breakdown: { name: string; count: number }[];
  monthly_trends: { month: string; count: number }[];
  officer_stats: { name: string; tests: number }[];
}

export interface AuditLogItem {
  id: number;
  event_id: string;
  user_name?: string;
  event_type: string;
  related_record_id?: string;
  details?: string;
  client_ip?: string;
  prev_event_hash?: string;
  event_hash: string;
  timestamp: string;
}
