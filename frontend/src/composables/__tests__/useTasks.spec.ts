import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useTasks } from '../useTasks'
import * as api from '../../services/api'

vi.mock('../../services/api', () => ({
  apiClient: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message)
      this.status = status
      this.name = 'ApiError'
    }
  }
}))

describe('useTasks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetchTasks updates tasks and totalTasks state', async () => {
    const mockTasks = [{ id: '1', title: 'Task 1' }]
    const mockTotal = 1
    ;(api.apiClient as any).mockResolvedValue({
      data: mockTasks,
      total: mockTotal
    })

    const { tasks, totalTasks, fetchTasks } = useTasks()
    
    expect(tasks.value).toEqual([])
    expect(totalTasks.value).toBe(0)

    await fetchTasks()

    expect(tasks.value).toEqual(mockTasks)
    expect(totalTasks.value).toBe(mockTotal)
    expect(api.apiClient).toHaveBeenCalledWith('/tasks')
  })

  it('updateTaskStatus calls PATCH and reconciles state', async () => {
    ;(api.apiClient as any).mockResolvedValue({ data: {} })
    const { updateTaskStatus } = useTasks()
    
    // We can't easily mock fetchTasks inside useTasks if it's not exported/injected,
    // but we can check if apiClient was called again for fetchTasks
    await updateTaskStatus('1', 'completed', 1)

    expect(api.apiClient).toHaveBeenCalledWith('/tasks/1/status', expect.objectContaining({
      method: 'PATCH',
      body: JSON.stringify({ status: 'completed', version: 1 })
    }))
    // The second call should be fetchTasks
    expect(api.apiClient).toHaveBeenLastCalledWith('/tasks')
  })

  it('updateTaskStatus reconciles state on 409 Conflict', async () => {
    const error = new api.ApiError(409, 'Conflict')
    ;(api.apiClient as any).mockRejectedValueOnce(error)
    ;(api.apiClient as any).mockResolvedValue({ data: [], total: 0 })

    const { updateTaskStatus, error: errorState } = useTasks()
    
    await expect(updateTaskStatus('1', 'completed', 1)).rejects.toThrow('Conflict')
    
    expect(errorState.value).toBe('Conflict')
    expect(api.apiClient).toHaveBeenCalledWith('/tasks')
  })

  it('updateTaskDetails calls PUT and reconciles state', async () => {
    ;(api.apiClient as any).mockResolvedValue({ data: {} })
    const { updateTaskDetails } = useTasks()
    
    await updateTaskDetails('1', { title: 'New Title' }, 1)

    expect(api.apiClient).toHaveBeenCalledWith('/tasks/1', expect.objectContaining({
      method: 'PUT',
      body: JSON.stringify({ title: 'New Title', version: 1 })
    }))
    expect(api.apiClient).toHaveBeenLastCalledWith('/tasks')
  })

  it('deleteTask calls DELETE with version and reconciles state', async () => {
    ;(api.apiClient as any).mockResolvedValue({ data: {} })
    const { deleteTask } = useTasks()
    
    await deleteTask('1', 5)

    expect(api.apiClient).toHaveBeenCalledWith('/tasks/1?version=5', expect.objectContaining({
      method: 'DELETE'
    }))
    expect(api.apiClient).toHaveBeenLastCalledWith('/tasks')
  })

  it('deleteTask reconciles state on 409 Conflict', async () => {
    const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {})
    const error = new api.ApiError(409, 'Conflict')
    ;(api.apiClient as any).mockRejectedValueOnce(error)
    ;(api.apiClient as any).mockResolvedValue({ data: [], total: 0 })

    const { deleteTask, error: errorState } = useTasks()
    
    await expect(deleteTask('1', 5)).rejects.toThrow('Conflict')
    
    expect(errorState.value).toBe('Conflict')
    expect(alertMock).toHaveBeenCalledWith(expect.stringContaining("Conflict"))
    expect(api.apiClient).toHaveBeenCalledWith('/tasks')
    alertMock.mockRestore()
  })

  it('fetchAllTaskOptions updates allTaskOptions state', async () => {
    const mockData = [
      { id: '1', title: 'Task 1', other: 'stuff' },
      { id: '2', title: 'Task 2' }
    ]
    ;(api.apiClient as any).mockResolvedValue({ data: mockData })

    const { allTaskOptions, fetchAllTaskOptions } = useTasks()
    
    await fetchAllTaskOptions()

    expect(allTaskOptions.value).toEqual([
      { id: '1', title: 'Task 1' },
      { id: '2', title: 'Task 2' }
    ])
    expect(api.apiClient).toHaveBeenCalledWith('/tasks?limit=10000')
  })
})

describe('useTasks OCC', () => {
  it('triggers window.alert on 409 conflict and refreshes (status update)', async () => {
    const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {})
    vi.mocked(api.apiClient).mockRejectedValue(new api.ApiError(409, "Version mismatch"))
    
    const { updateTaskStatus } = useTasks()
    
    await expect(updateTaskStatus('1', 'Completed', 1)).rejects.toThrow()
    expect(alertMock).toHaveBeenCalledWith(expect.stringContaining("modified by someone else"))
    
    alertMock.mockRestore()
  })

  it('triggers window.alert on 409 conflict and refreshes (details update)', async () => {
    const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {})
    vi.mocked(api.apiClient).mockRejectedValue(new api.ApiError(409, "Version mismatch"))
    
    const { updateTaskDetails } = useTasks()
    
    await expect(updateTaskDetails('1', { title: 'New Title' }, 1)).rejects.toThrow()
    expect(alertMock).toHaveBeenCalledWith(expect.stringContaining("modified by someone else"))
    
    alertMock.mockRestore()
  })
})
