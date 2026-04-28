<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits(['update:modelValue'])

const frequency = ref('')
const interval = ref(1)

onMounted(() => {
  if (props.modelValue) {
    if (props.modelValue.includes('FREQ=DAILY')) frequency.value = 'DAILY'
    else if (props.modelValue.includes('FREQ=WEEKLY')) frequency.value = 'WEEKLY'
    else if (props.modelValue.includes('FREQ=MONTHLY')) frequency.value = 'MONTHLY'
    else frequency.value = 'CUSTOM'
  }
})

watch([frequency, interval], () => {
  if (!frequency.value) {
    emit('update:modelValue', '')
    return
  }
  if (frequency.value === 'CUSTOM') return
  
  let rule = `FREQ=${frequency.value}`
  if (interval.value > 1) rule += `;INTERVAL=${interval.value}`
  emit('update:modelValue', rule)
})
</script>

<template>
  <div class="space-y-2 border p-3 rounded bg-gray-50">
    <div class="flex gap-2 items-center text-gray-700">
      <select v-model="frequency" class="border p-2 rounded text-sm flex-grow bg-white">
        <option value="">Does not repeat</option>
        <option value="DAILY">Daily</option>
        <option value="WEEKLY">Weekly</option>
        <option value="MONTHLY">Monthly</option>
        <option value="CUSTOM">Custom (Raw RRULE)</option>
      </select>
      
      <div v-if="frequency && frequency !== 'CUSTOM'" class="flex items-center gap-2">
        <span class="text-sm text-gray-600 font-medium">Every</span>
        <input type="number" v-model="interval" min="1" class="border p-1 rounded w-16 text-sm text-center">
        <span class="text-sm text-gray-600 font-medium">
          {{ frequency === 'DAILY' ? 'days' : frequency === 'WEEKLY' ? 'weeks' : 'months' }}
        </span>
      </div>
    </div>
    
    <div v-if="frequency === 'CUSTOM' || frequency !== ''">
      <input 
        :value="modelValue" 
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        placeholder="e.g. FREQ=WEEKLY;BYDAY=MO" 
        class="w-full border p-2 rounded text-sm font-mono text-gray-700 bg-white"
        :readonly="frequency !== 'CUSTOM'"
      >
    </div>
  </div>
</template>
