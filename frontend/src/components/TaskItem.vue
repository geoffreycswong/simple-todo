<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ task: any }>()
defineEmits(['update-status', 'edit', 'delete'])

const dueDateColor = computed(() => {
  if (!props.task.due_date) return ''
  const due = new Date(props.task.due_date).setHours(0, 0, 0, 0)
  const today = new Date().setHours(0, 0, 0, 0)
  
  if (due < today) return 'bg-red-100 text-red-800'
  if (due === today) return 'bg-yellow-100 text-yellow-800'
  return 'bg-green-100 text-green-800'
})

const formattedDueDate = computed(() => {
  if (!props.task.due_date) return ''
  return new Date(props.task.due_date).toLocaleDateString()
})
</script>

<template>
  <div class="p-4 bg-white shadow rounded flex justify-between items-center" :class="{ 'opacity-50': task.is_blocked }">
    <div class="flex-grow">
      <h3 class="font-bold" :class="{'line-through text-gray-400': task.deleted_at}">{{ task.title }}</h3>
      <p class="text-sm text-gray-600">{{ task.description }}</p>
      <div class="mt-2 flex flex-wrap gap-2">
        <span class="px-2 py-1 text-xs bg-blue-100 rounded">{{ task.status }}</span>
        <span v-if="task.is_blocked" class="px-2 py-1 text-xs bg-red-100 rounded">Blocked</span>
        <span class="px-2 py-1 text-xs bg-gray-100 rounded">P: {{ task.priority }}</span>
        <span v-if="task.due_date" 
              class="px-2 py-1 text-xs rounded font-medium" 
              :class="dueDateColor"
              data-testid="due-date-badge">
          Due: {{ formattedDueDate }}
        </span>
      </div>
    </div>
    
    <div v-if="!task.deleted_at" class="flex gap-2 shrink-0">
      <button 
        v-if="task.status === 'Not Started'"
        @click="$emit('update-status', task.id, 'In Progress', task.version)"
        :disabled="task.is_blocked"
        class="px-3 py-1 bg-green-500 text-white rounded text-sm disabled:bg-gray-300"
      >
        Start
      </button>
      <button 
        v-if="task.status === 'In Progress'"
        @click="$emit('update-status', task.id, 'Completed', task.version)"
        class="px-3 py-1 bg-blue-500 text-white rounded text-sm"
      >
        Complete
      </button>
      <button @click="$emit('edit', task)" class="px-3 py-1 border border-blue-500 text-blue-500 rounded text-sm">
        Edit
      </button>
      <button @click="$emit('delete', task.id)" class="px-3 py-1 border border-red-500 text-red-500 rounded text-sm">
        Del
      </button>
    </div>
    <div v-else class="text-sm text-gray-500 italic">Deleted</div>
  </div>
</template>
