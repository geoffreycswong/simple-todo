<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useTasks } from '../composables/useTasks'
import TaskItem from './TaskItem.vue'
import FilterBar from './FilterBar.vue'

const { tasks, totalTasks, fetchTasks, updateTaskStatus, deleteTask, error } = useTasks()
const currentPage = ref(1)
const pageSize = 10
const currentFilters = ref({})

const load = () => {
  fetchTasks({ 
    skip: (currentPage.value - 1) * pageSize, 
    limit: pageSize,
    ...currentFilters.value
  })
}

const applyFilters = (filters: any) => {
  currentFilters.value = filters
  currentPage.value = 1 // Reset to page 1 on filter change
  load()
}

onMounted(load)
watch(currentPage, load)

defineEmits(['edit-task'])
</script>

<template>
  <div>
    <FilterBar @filter="applyFilters" />
    
    <div v-if="error" class="p-4 mb-4 bg-red-100 text-red-700 rounded">{{ error }}</div>
    
    <div class="space-y-4">
      <div v-for="task in tasks" :key="task.id">
        <TaskItem 
          :task="task" 
          @update-status="updateTaskStatus" 
          @edit="$emit('edit-task', task)"
          @delete="(id) => deleteTask(id, task.version)"
        />
      </div>
    </div>

    <div class="flex justify-center items-center gap-4 mt-8">
      <button 
        :disabled="currentPage === 1" 
        @click="currentPage--"
        class="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
      >
        Prev
      </button>
      <span class="text-sm font-medium">Page {{ currentPage }} of {{ Math.ceil(totalTasks / pageSize) || 1 }}</span>
      <button 
        :disabled="currentPage * pageSize >= totalTasks" 
        @click="currentPage++"
        class="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
      >
        Next
      </button>
    </div>
  </div>
</template>
