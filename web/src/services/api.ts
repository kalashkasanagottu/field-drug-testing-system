import {
  User, TestKit, TestRecordSummary, TestRecordDetail, DashboardStats, AuditLogItem
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

class ApiService {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('forensic_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('forensic_token', token);
    } else {
      localStorage.removeItem('forensic_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) errorMsg = errJson.detail;
      } catch (e) {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return response.json();
  }

  // --- Auth ---
  async login(username: string, password: string):Promise<any> {
    const data = await this.request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.setToken(data.access_token);
    return data;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } catch (e) {
      // ignore
    }
    this.setToken(null);
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // --- Kits ---
  async getKits(): Promise<TestKit[]> {
    return this.request<TestKit[]>('/kits');
  }

  async createKit(kitData: any): Promise<TestKit> {
    return this.request<TestKit>('/kits', {
      method: 'POST',
      body: JSON.stringify(kitData)
    });
  }

  // --- Tests ---
  async createTest(testData: any): Promise<TestRecordDetail> {
    return this.request<TestRecordDetail>('/tests', {
      method: 'POST',
      body: JSON.stringify(testData)
    });
  }

  async captureAndAnalyze(testId: string, imageFile?: File, imageBase64?: string): Promise<any> {
    const formData = new FormData();
    if (imageFile) {
      formData.append('file', imageFile);
    } else if (imageBase64) {
      formData.append('image_base64', imageBase64);
    }
    return this.request<any>(`/tests/${testId}/capture`, {
      method: 'POST',
      body: formData
    });
  }

  async getTests(params: {
    q?: string;
    classification?: string;
    kit_id?: number;
    verification_status?: string;
    sync_status?: string;
  } = {}): Promise<TestRecordSummary[]> {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.classification) query.append('classification', params.classification);
    if (params.kit_id) query.append('kit_id', params.kit_id.toString());
    if (params.verification_status) query.append('verification_status', params.verification_status);
    if (params.sync_status) query.append('sync_status', params.sync_status);

    return this.request<TestRecordSummary[]>(`/tests?${query.toString()}`);
  }

  async getTestDetail(testId: string): Promise<TestRecordDetail> {
    return this.request<TestRecordDetail>(`/tests/${testId}`);
  }

  // --- Evidence Verification ---
  async verifyEvidence(testId: string, checkImage = true, checkSignature = true): Promise<any> {
    return this.request<any>(`/evidence/${testId}/verify`, {
      method: 'POST',
      body: JSON.stringify({
        test_id: testId,
        check_image_tampering: checkImage,
        check_digital_signature: checkSignature
      })
    });
  }

  async simulateTampering(testId: string): Promise<any> {
    return this.request<any>(`/evidence/${testId}/simulate-tampering`, {
      method: 'POST'
    });
  }

  async getPublicKey(): Promise<any> {
    return this.request<any>('/evidence/public-key');
  }

  // --- Reports ---
  async generateReport(testId: string): Promise<any> {
    return this.request<any>(`/reports/${testId}/generate`, {
      method: 'POST'
    });
  }

  getReportDownloadUrl(testId: string): string {
    return `${API_BASE}/reports/${testId}/download`;
  }

  // --- Analytics & Admin ---
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/analytics/dashboard');
  }

  async getAuditLogs(limit = 100): Promise<AuditLogItem[]> {
    return this.request<AuditLogItem[]>(`/admin/audit-logs?limit=${limit}`);
  }

  async getSystemHealth(): Promise<any> {
    return this.request<any>('/admin/system-health');
  }

  async getUsers(): Promise<User[]> {
    return this.request<User[]>('/admin/users');
  }

  async createUser(userData: any): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async toggleUserActive(userId: number): Promise<any> {
    return this.request<any>(`/admin/users/${userId}/toggle-active`, {
      method: 'PUT'
    });
  }

  // --- Calibration Profiles ---
  async getCalibrationProfiles(kitId?: number): Promise<any[]> {
    const query = kitId ? `?kit_id=${kitId}` : '';
    return this.request<any[]>(`/kits/${kitId}/profiles${query}`);
  }

  async createCalibrationProfile(kitId: number, profileData: any): Promise<any> {
    return this.request<any>(`/kits/${kitId}/profiles`, {
      method: 'POST',
      body: JSON.stringify(profileData)
    });
  }

  // --- System Settings ---
  async getSystemSettings(): Promise<any> {
    return this.request<any>('/admin/system-health');
  }

  // --- Reports ---
  async getReports(): Promise<any[]> {
    // List reports from the reports directory via backend
    return this.request<any[]>('/reports');
  }
}

export const api = new ApiService();
