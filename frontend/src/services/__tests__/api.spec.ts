import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient, ApiError } from '../api'

describe('apiClient', () => {
  const fetchMock = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('fetch', fetchMock)
  })

  it('throws ApiError with 409 status on conflict', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 409,
      headers: new Map([['content-type', 'application/json']]),
      json: () => Promise.resolve({ detail: 'Version mismatch' })
    })

    await expect(apiClient('/tasks')).rejects.toThrow(ApiError)
  })

  it('prefixes endpoint with /api/v1', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      json: () => Promise.resolve({ success: true })
    })

    await apiClient('/tasks')
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/tasks', expect.any(Object))
  })

  it('parses JSON response correctly', async () => {
    const mockData = { id: 1, title: 'Test Task' }
    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      json: () => Promise.resolve(mockData)
    })

    const result = await apiClient('/tasks/1')
    expect(result.data).toEqual(mockData)
  })

  it('extracts X-Total-Count header', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      headers: new Map([
        ['content-type', 'application/json'],
        ['X-Total-Count', '42']
      ]),
      json: () => Promise.resolve([])
    })

    const result = await apiClient('/tasks')
    expect(result.total).toBe(42)
  })
})
