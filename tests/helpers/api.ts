/**
 * API Helper for Integration Tests
 */

import axios, { AxiosInstance } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:8000/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      response => response.data,
      error => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  async get(path: string, params?: any) {
    return this.client.get(path, { params });
  }

  async post(path: string, data?: any) {
    return this.client.post(path, data);
  }

  async put(path: string, data?: any) {
    return this.client.put(path, data);
  }

  async patch(path: string, data?: any) {
    return this.client.patch(path, data);
  }

  async delete(path: string) {
    return this.client.delete(path);
  }

  async uploadFile(path: string, file: File | Buffer, filename: string, mimeType: string) {
    const formData = new FormData();
    formData.append('files', new Blob([file], { type: mimeType }), filename);
    
    return this.client.post(path, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
}

export const api = new ApiClient();