<script setup lang="ts">
import { ref, onMounted } from 'vue'
import TaskList from './components/TaskList.vue'
import TaskFormModal from './components/TaskFormModal.vue'
import { useTasks } from './composables/useTasks'
import { apiClient } from './services/api'

const isModalOpen = ref(false)
const taskToEdit = ref<any>(null)
const { fetchTasks, allTaskOptions, fetchAllTaskOptions, updateTaskDetails, isLoading, tasks } = useTasks()

const openNewTaskModal = () => {
  taskToEdit.value = null
  isModalOpen.value = true
}

const openEditTaskModal = async (task: any) => {
  try {
    // 1. Refresh dependencies so deleted tasks drop off the dropdown list
    await fetchAllTaskOptions()
    
    // 2. Refresh the main task list to ensure we have the latest version of the task
    await fetchTasks()
    
    // 3. Find the freshest version of the task to edit
    const freshestTask = tasks.value.find(t => t.id === task.id)
    
    if (!freshestTask) {
      window.alert("This task has been deleted and cannot be edited.")
      return
    }
    
    taskToEdit.value = freshestTask
    isModalOpen.value = true
  } catch (error) {
    console.error("Failed to prepare edit modal:", error)
  }
}

const handleSubmit = async (payload: any) => {
  try {
    if (taskToEdit.value) {
      await updateTaskDetails(taskToEdit.value.id, payload, taskToEdit.value.version)
    } else {
      await apiClient('/tasks', { method: 'POST', body: JSON.stringify(payload) })
    }
    isModalOpen.value = false
    await fetchTasks()         // Refresh list dynamically (SPA pattern)
    await fetchAllTaskOptions() // Refresh options for dependency lookup
  } catch (error) {
    console.error("Failed to submit task:", error)
  }
}

onMounted(() => {
  fetchAllTaskOptions()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-4 md:p-8">
    <div class="max-w-3xl mx-auto">
      <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">SimpleTodo</h1>
        <button @click="openNewTaskModal" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
          + New Task
        </button>
      </div>
      
      <TaskList @edit-task="openEditTaskModal" />
      
      <div v-if="isLoading" class="fixed inset-0 bg-white bg-opacity-50 flex items-center justify-center z-[60]">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
      
      <TaskFormModal 
        :is-open="isModalOpen" 
        :all-tasks="allTaskOptions"
        :task-to-edit="taskToEdit"
        @close="isModalOpen = false"
        @submit="handleSubmit"
      />
    </div>
  </div>
</template>
