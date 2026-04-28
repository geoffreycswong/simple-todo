export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export interface ApiResponse<T> {
  data: T;
  total?: number;
}

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const response = await fetch(`/api/v1${endpoint}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });

  const contentType = response.headers.get('content-type');
  let data;
  
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMsg = typeof data === 'object' && data.detail ? data.detail : (data || response.statusText);
    throw new ApiError(response.status, typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
  }

  const total = response.headers.get('X-Total-Count');
  return {
    data: data as T,
    total: total ? parseInt(total, 10) : undefined
  };
}
