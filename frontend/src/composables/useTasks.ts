import { ref } from 'vue'
import { apiClient, ApiError } from '../services/api'

// GLOBAL STATE (Singleton)
const tasks = ref<any[]>([])
const totalTasks = ref(0)
const allTaskOptions = ref<any[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const currentParams = ref<any>({}) // Stores active filters & pagination

export function useTasks() {
  const fetchTasks = async (params?: any) => {
    isLoading.value = true
    error.value = null
    
    // OVERWRITE entirely instead of merging, so cleared filters are actually removed
    if (params) {
      currentParams.value = params 
    }
    
    try {
      const queryString = new URLSearchParams(currentParams.value).toString()
      const { data, total } = await apiClient<any[]>('/tasks' + (queryString ? '?' + queryString : ''))
      tasks.value = data
      if (total !== undefined) totalTasks.value = total
    } catch (e: any) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  const updateTaskStatus = async (id: string, status: string, version: number) => {
    try {
      await apiClient(`/tasks/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, version })
      })
      // Refresh using current parameters
      await fetchTasks() 
    } catch (e: any) {
      if (e instanceof ApiError && (e.status === 409 || e.status === 404)) {
        await fetchTasks() // Reconcile
        const msg = e.status === 404 
          ? "Error: This task has been deleted by someone else." 
          : "Conflict: This task was modified by someone else.";
        window.alert(`${msg} Your view has been updated with the latest data.`)
        error.value = e.message
      } else if (e instanceof ApiError && e.status === 422) {
        await fetchTasks() // Reconcile
        error.value = e.message
      }
      throw e
    }
  }

  const updateTaskDetails = async (id: string, payload: any, version: number) => {
    try {
      await apiClient(`/tasks/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ ...payload, version })
      })
      // Refresh using current parameters
      await fetchTasks()
    } catch (e: any) {
      if (e instanceof ApiError && (e.status === 409 || e.status === 404)) {
        await fetchTasks() // Reconcile
        const msg = e.status === 404 
          ? "Error: This task has been deleted by someone else." 
          : "Conflict: This task was modified by someone else.";
        window.alert(`${msg} Your view has been updated with the latest data.`)
        error.value = e.message
      } else if (e instanceof ApiError && e.status === 422) {
        await fetchTasks() // Reconcile
        error.value = e.message
      }
      throw e
    }
  }

  const deleteTask = async (id: string, version: number) => {
    try {
      await apiClient(`/tasks/${id}?version=${version}`, { method: 'DELETE' })
      // Refresh using current parameters
      await fetchTasks()
    } catch (e: any) {
      if (e instanceof ApiError && (e.status === 409 || e.status === 404)) {
        await fetchTasks() // Reconcile
        const msg = e.status === 404 
          ? "Error: This task has been deleted by someone else." 
          : "Conflict: This task was modified by someone else.";
        window.alert(`${msg} The list will now refresh to show the latest version.`)
        error.value = e.message
      } else {
        error.value = e.message
      }
      throw e
    }
  }

  const fetchAllTaskOptions = async () => {
    try {
      // Fetch unpaginated lightweight list for dependency dropdowns
      const { data } = await apiClient<any[]>('/tasks?limit=10000')
      allTaskOptions.value = data.map((t: any) => ({ id: t.id, title: t.title }))
    } catch (e: any) {
      console.error("Failed to fetch task options:", e)
    }
  }

  return { 
    tasks, 
    totalTasks, 
    allTaskOptions, 
    isLoading, 
    error, 
    currentParams,
    fetchTasks, 
    updateTaskStatus, 
    updateTaskDetails, 
    deleteTask, 
    fetchAllTaskOptions 
  }
}
