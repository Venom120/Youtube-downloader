import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { BACKEND_URL, APP_ID } from "./config";

/**
 * Axios client configured with app ID authentication
 */
class BackendClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BACKEND_URL,
      timeout: 30000, // 30 seconds
      headers: {
        "Content-Type": "application/json",
        "X-App-ID": APP_ID, // Custom header for backend authentication
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[Backend API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error("[Backend API] Request error:", error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[Backend API] Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        if (error.response) {
          // Server responded with error status
          console.error(`[Backend API] Error ${error.response.status}:`, error.response.data);
          
          if (error.response.status === 403) {
            console.error("[Backend API] Forbidden: Invalid App ID");
          }
        } else if (error.request) {
          // Request made but no response received
          console.error("[Backend API] No response received:", error.message);
        } else {
          // Error in request configuration
          console.error("[Backend API] Request setup error:", error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  /**
   * POST request
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  /**
   * Get raw axios instance for custom configurations
   */
  getInstance(): AxiosInstance {
    return this.client;
  }
}

// Export singleton instance
export const backendClient = new BackendClient();
export default backendClient;
