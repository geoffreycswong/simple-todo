<script setup lang="ts">
import { reactive, watch } from 'vue'

const emit = defineEmits(['filter'])
const filters = reactive({ 
  status: '', 
  priority: '', 
  is_blocked: '', 
  is_deleted: '', 
  sort_by: 'due_date', 
  order: 'asc' 
})

watch(filters, (newFilters) => {
  // Clean empty strings to avoid sending `status=` in query params
  const payload = Object.fromEntries(Object.entries(newFilters).filter(([_, v]) => v !== ''))
  emit('filter', payload)
}, { deep: true })
</script>

<template>
  <div class="p-4 bg-gray-100 rounded flex flex-wrap gap-4 mb-6">
    <select v-model="filters.status" class="p-2 border rounded bg-white text-sm">
      <option value="">All Statuses</option>
      <option value="Not Started">Not Started</option>
      <option value="In Progress">In Progress</option>
      <option value="Completed">Completed</option>
    </select>
    <select v-model="filters.priority" class="p-2 border rounded bg-white text-sm">
      <option value="">All Priorities</option>
      <option value="Low">Low</option>
      <option value="Medium">Medium</option>
      <option value="High">High</option>
    </select>
    <select v-model="filters.is_blocked" class="p-2 border rounded bg-white text-sm">
      <option value="">All Dependency States</option>
      <option :value="true">Blocked</option>
      <option :value="false">Unblocked</option>
    </select>
    <select v-model="filters.is_deleted" class="p-2 border rounded bg-white text-sm">
      <option value="">Active Tasks</option>
      <option value="true">Show Deleted Tasks</option>
    </select>
    <div class="flex items-center gap-2 ml-auto">
      <span class="text-sm font-medium text-gray-700">Sort By:</span>
      <select v-model="filters.sort_by" class="p-2 border rounded bg-white text-sm">
        <option value="due_date">Due Date</option>
        <option value="priority">Priority</option>
        <option value="status">Status</option>
        <option value="name">Name</option>
      </select>
      <select v-model="filters.order" class="p-2 border rounded bg-white text-sm">
        <option value="asc">Ascending</option>
        <option value="desc">Descending</option>
      </select>
    </div>
  </div>
</template>
