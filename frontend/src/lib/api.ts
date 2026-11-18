export const BACKEND_BASE_URL =
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  '';

interface RequestOptions extends RequestInit {
  token?: string | null;
  organizationId?: string | null;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: any[];
  requestId?: string;

  constructor(code: string, message: string, status: number, details: any[] = [], requestId?: string) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
    this.requestId = requestId;
  }
}

export async function apiClient<T = any>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { token, organizationId, headers = {}, ...rest } = options;

  // Resolve token and organizationId with fallback to localStorage
  const effectiveToken =
    token !== undefined
      ? token
      : typeof window !== 'undefined'
      ? localStorage.getItem('marketpath_auth_token')
      : null;

  const effectiveOrgId =
    organizationId !== undefined
      ? organizationId
      : typeof window !== 'undefined'
      ? localStorage.getItem('marketpath_active_org_id')
      : null;

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(headers as Record<string, string>),
  };

  if (effectiveToken) {
    requestHeaders['Authorization'] = `Bearer ${effectiveToken}`;
  }

  if (effectiveOrgId) {
    requestHeaders['X-Organization-Id'] = effectiveOrgId;
  }

  let resolvedPath = path;
  if (resolvedPath.startsWith('/api/v1/admin')) {
    try {
      const rawUser = typeof window !== 'undefined' ? localStorage.getItem('marketpath_auth_user') : null;
      const authUser = rawUser ? JSON.parse(rawUser) : null;
      if (
        authUser &&
        !authUser.is_platform_admin &&
        (authUser.account_type === 'admin' || authUser.email === 'demo.admin@marketpath.ai')
      ) {
        resolvedPath = resolvedPath.replace('/api/v1/admin', '/api/v1/demo-admin');
      }
    } catch {
      // Ignore parse errors
    }
  }

  const endpoint = resolvedPath.startsWith('http') ? resolvedPath : `${BACKEND_BASE_URL}${resolvedPath}`;

  let response: Response;
  try {
    response = await fetch(endpoint, {
      credentials: 'include',
      ...rest,
      headers: requestHeaders,
    });
  } catch (netErr: any) {
    const errorMsg =
      netErr?.message === 'Failed to fetch' || netErr?.name === 'TypeError'
        ? `Cannot connect to MarketPath server at ${endpoint || 'the local backend'}. Please verify the backend service is running on port 8000.`
        : netErr?.message || 'Network request failed.';
    throw new ApiError('NETWORK_ERROR', errorMsg, 0);
  }

  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const errorPayload = data?.error;
    const detailMsg = data?.detail || (typeof data === 'string' ? data : null);
    throw new ApiError(
      errorPayload?.code || 'API_ERROR',
      errorPayload?.message || detailMsg || response.statusText || 'Request failed',
      response.status,
      errorPayload?.details || [],
      errorPayload?.request_id
    );
  }

  return data as T;
}


