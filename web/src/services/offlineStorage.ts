import { api } from './api';

export interface QueuedTest {
  client_uuid: string;
  created_at: string;
  kit_id: number;
  kit_name: string;
  kit_batch_number: string;
  case_reference?: string;
  notes?: string;
  gps_latitude?: number;
  gps_longitude?: number;
  gps_accuracy_meters?: number;
  image_base64?: string;
  status: 'SAVED_LOCALLY' | 'PENDING_SYNC' | 'SYNCHRONIZING' | 'SYNCHRONIZED' | 'FAILED';
  error_message?: string;
  server_test_id?: string;
}

const STORAGE_KEY = 'forensic_offline_queue';

class OfflineStorageService {
  private isSimulatedOffline = false;

  getIsOffline(): boolean {
    return this.isSimulatedOffline || !navigator.onLine;
  }

  setSimulatedOffline(offline: boolean) {
    this.isSimulatedOffline = offline;
  }

  getQueuedTests(): QueuedTest[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  saveQueuedTests(tests: QueuedTest[]) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tests));
  }

  enqueueTest(test: Omit<QueuedTest, 'client_uuid' | 'created_at' | 'status'>): QueuedTest {
    const queue = this.getQueuedTests();
    const newEntry: QueuedTest = {
      ...test,
      client_uuid: 'LOCAL-' + Math.random().toString(36).substring(2, 9).toUpperCase(),
      created_at: new Date().toISOString(),
      status: 'SAVED_LOCALLY'
    };
    queue.unshift(newEntry);
    this.saveQueuedTests(queue);
    return newEntry;
  }

  updateTestStatus(client_uuid: string, status: QueuedTest['status'], server_test_id?: string, error?: string) {
    const queue = this.getQueuedTests();
    const idx = queue.findIndex(t => t.client_uuid === client_uuid);
    if (idx !== -1) {
      queue[idx].status = status;
      if (server_test_id) queue[idx].server_test_id = server_test_id;
      if (error) queue[idx].error_message = error;
      this.saveQueuedTests(queue);
    }
  }

  async syncAllPending(onProgress?: (syncedCount: number, total: number) => void): Promise<{ success: number; failed: number }> {
    if (this.getIsOffline()) {
      throw new Error('Device is offline. Connect to network before synchronizing.');
    }

    const queue = this.getQueuedTests();
    const pending = queue.filter(t => t.status === 'SAVED_LOCALLY' || t.status === 'FAILED');
    let success = 0;
    let failed = 0;

    for (let i = 0; i < pending.length; i++) {
      const item = pending[i];
      this.updateTestStatus(item.client_uuid, 'SYNCHRONIZING');

      try {
        // Step 1: Create record with idempotency UUID
        const created = await api.createTest({
          case_reference: item.case_reference,
          kit_id: item.kit_id,
          kit_batch_number: item.kit_batch_number,
          notes: item.notes,
          gps_latitude: item.gps_latitude,
          gps_longitude: item.gps_longitude,
          gps_accuracy_meters: item.gps_accuracy_meters,
          device_timestamp: item.created_at,
          client_uuid: item.client_uuid
        });

        // Step 2: Upload captured image if available
        if (item.image_base64) {
          await api.captureAndAnalyze(created.test_id, undefined, item.image_base64);
        }

        this.updateTestStatus(item.client_uuid, 'SYNCHRONIZED', created.test_id);
        success++;
      } catch (err: any) {
        this.updateTestStatus(item.client_uuid, 'FAILED', undefined, err.message || 'Sync failed');
        failed++;
      }

      if (onProgress) {
        onProgress(i + 1, pending.length);
      }
    }

    return { success, failed };
  }

  clearSynced() {
    const queue = this.getQueuedTests();
    const remaining = queue.filter(t => t.status !== 'SYNCHRONIZED');
    this.saveQueuedTests(remaining);
  }
}

export const offlineStorage = new OfflineStorageService();
