<script setup lang="ts">
import { reactive, watch } from 'vue'
import RRuleGenerator from './RRuleGenerator.vue'

const props = defineProps<{ isOpen: boolean, allTasks: any[], taskToEdit: any }>()
const emit = defineEmits(['close', 'submit'])

const form = reactive({
  title: '',
  description: '',
  priority: 'Medium',
  due_date: '',
  recurrence_rule: '',
  recurrence_anchor: 'DUE_DATE',
  dependency_ids: []
})

watch(() => props.taskToEdit, (newVal) => {
  if (newVal) {
    // Strictly map only the fields that belong in the form
    form.title = newVal.title || ''
    form.description = newVal.description || ''
    form.priority = newVal.priority || 'Medium'
    form.due_date = newVal.due_date ? newVal.due_date.split('T')[0] : ''
    form.recurrence_rule = newVal.recurrence_rule || ''
    form.recurrence_anchor = newVal.recurrence_anchor || 'DUE_DATE'
    form.dependency_ids = newVal.dependency_ids || []
    
    // Explicitly clean up any stray fields if Vue accidentally retained them
    delete (form as any).status
    delete (form as any).id
  } else {
    // Reset to a pristine default state
    form.title = ''
    form.description = ''
    form.priority = 'Medium'
    form.due_date = ''
    form.recurrence_rule = ''
    form.recurrence_anchor = 'DUE_DATE'
    form.dependency_ids = []
    
    // Clean up polluted fields
    delete (form as any).status
    delete (form as any).id
  }
}, { immediate: true })

const submit = () => {
  emit('submit', { 
    ...form, 
    due_date: form.due_date ? new Date(form.due_date).toISOString() : null,
    version: props.taskToEdit?.version
  })
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white p-6 rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
      <h2 class="text-xl font-bold mb-4">{{ taskToEdit ? 'Edit Task' : 'New Task' }}</h2>
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Title</label>
          <input v-model="form.title" class="w-full border p-2 rounded">
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Description</label>
          <textarea v-model="form.description" class="w-full border p-2 rounded h-20"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Priority</label>
            <select v-model="form.priority" class="w-full border p-2 rounded">
              <option>Low</option><option>Medium</option><option>High</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Due Date</label>
            <input type="date" v-model="form.due_date" class="w-full border p-2 rounded">
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Recurrence Rule (RRULE)</label>
          <RRuleGenerator v-model="form.recurrence_rule" />
        </div>
        <div v-if="form.recurrence_rule">
          <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Recurrence Anchor</label>
          <select v-model="form.recurrence_anchor" class="w-full border p-2 rounded text-sm">
            <option value="DUE_DATE">Due Date</option>
            <option value="COMPLETION_DATE">Completion Date</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Dependencies</label>
          <select v-model="form.dependency_ids" multiple class="w-full border p-2 rounded h-24 text-sm">
            <option v-for="t in allTasks" :key="t.id" :value="t.id" :disabled="t.id === taskToEdit?.id">
              {{ t.title }}
            </option>
          </select>
        </div>
      </div>
      <div class="mt-6 flex justify-end gap-2">
        <button @click="$emit('close')" class="px-4 py-2 border rounded text-sm font-medium">Cancel</button>
        <button @click="submit" class="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium">
          {{ taskToEdit ? 'Save Changes' : 'Create Task' }}
        </button>
      </div>
    </div>
  </div>
</template>
