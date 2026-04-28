# TODO Application: UX & Stability Implementation Plan



**For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement due date color-coding, a Vue-native RRULE generator, OCC protections for the delete operation, and read-only states for deleted tasks.

### Task 1: Backend - Add OCC Protection to Delete Operation

**Files:**
- Modify: `backend/app/crud.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_occ.py`

- [ ] **Step 1: Write TDD test for Delete OCC**
In `backend/tests/test_occ.py`, add:
```python
def test_delete_occ_conflict(client, db_session):
   task = client.post("/api/v1/tasks", json={"title": "Delete OCC Test"}).json()
  
   # Simulate another user deleting/updating it first (bumping version)
   client.put(f"/api/v1/tasks/{task['id']}", json={"title": "Updated", "version": task["version"]})
  
   # Try to delete with original stale version
   response = client.delete(f"/api/v1/tasks/{task['id']}?version={task['version']}")
   assert response.status_code == 409
```

- [ ] **Step 2: Update `crud.delete_todo`**
Modify `delete_todo` in `backend/app/crud.py` to enforce the version check:
```python
def delete_todo(db: Session, todo_id: uuid.UUID, version: int):
   db_todo = get_todo(db, todo_id)
   if not db_todo:
       return None
  
   if db_todo.version != version:
       raise VersionMismatchError("Task version mismatch")
  
   db_todo.deleted_at = datetime.utcnow()
   db.commit()
   return db_todo
```

- [ ] **Step 3: Update FastAPI Router**
Modify the `DELETE` endpoint in `backend/app/main.py`:
```python
@app.delete("/api/v1/tasks/{task_id}", status_code=204)
def delete_task(task_id: uuid.UUID, version: int, db: Session = Depends(get_db)):
   try:
       todo = crud.delete_todo(db=db, todo_id=task_id, version=version)
       if todo is None:
           raise HTTPException(status_code=404, detail="Task not found")
       return Response(status_code=204)
   except crud.VersionMismatchError as e:
       raise HTTPException(status_code=409, detail=str(e))
```

- [ ] **Step 4: Run backend tests and commit**
Run: `pytest backend/tests/test_occ.py`
Commit: `git add backend/ && git commit -m "fix(backend): enforce OCC on delete endpoint"`

---

### Task 2: Frontend - Delete OCC & Re-rendering

**Files:**
- Modify: `frontend/src/composables/useTasks.ts`
- Modify: `frontend/src/components/TaskList.vue`

- [ ] **Step 1: Update `deleteTask` in `useTasks.ts`**
Update the function to accept `version`, append it to the URL, and handle the 409 alert:
```typescript
 const deleteTask = async (id: string, version: number) => {
   try {
     await apiClient(`/tasks/${id}?version=${version}`, { method: 'DELETE' })
     await fetchTasks()
   } catch (e: any) {
     if (e instanceof ApiError && e.status === 409) {
       await fetchTasks()
       window.alert("Conflict: This task was modified by someone else. The list will now refresh to show the latest version.")
       error.value = e.message
     }
     throw e
   }
 }
```

- [ ] **Step 2: Update `TaskList.vue` to pass version**
In `frontend/src/components/TaskList.vue`, update the `@delete` binding:
```html
<TaskItem
 :task="task"
 @update-status="updateTaskStatus"
 @edit="$emit('edit-task', task)"
 @delete="(id) => deleteTask(id, task.version)"
/>
```

- [ ] **Step 3: Commit**
Commit: `git add frontend/ && git commit -m "fix(frontend): handle OCC alerts for deletes and refresh state"`

---

### Task 3: TaskItem Due Date UI & Read-Only State

**Files:**
- Modify: `frontend/src/components/__tests__/TaskItem.spec.ts`
- Modify: `frontend/src/components/TaskItem.vue`

- [ ] **Step 1: Write TDD tests for TaskItem rendering**
In `TaskItem.spec.ts`, assert that:
1. Buttons are hidden when `task.deleted_at` is populated.
2. A past due date applies the `bg-red-100` class.

- [ ] **Step 2: Implement Due Date Logic and UI in `TaskItem.vue`**
```vue
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ task: any }>()
defineEmits(['update-status', 'edit', 'delete'])

const dueDateColor = computed(() => {
 if (!props.task.due_date) return ''
 const due = new Date(props.task.due_date).setHours(0,0,0,0)
 const today = new Date().setHours(0,0,0,0)
  if (due < today) return 'bg-red-100 text-red-800 border-red-200'
 if (due === today) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
 return 'bg-green-100 text-green-800 border-green-200'
})

const formattedDueDate = computed(() => {
 if (!props.task.due_date) return ''
 return new Date(props.task.due_date).toLocaleDateString()
})
</script>

<template>
 <div class="p-4 bg-white shadow rounded flex justify-between items-center" :class="{ 'opacity-50': task.is_blocked }">
   <div class="flex-grow">
     <h3 class="font-bold text-lg" :class="{'line-through text-gray-400': task.deleted_at}">{{ task.title }}</h3>
     <p class="text-sm text-gray-600 mt-1">{{ task.description }}</p>
    
     <div class="mt-3 flex flex-wrap gap-2 items-center">
       <span class="px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">{{ task.status }}</span>
       <span class="px-2 py-1 text-xs font-semibold bg-gray-100 text-gray-800 rounded">P: {{ task.priority }}</span>
      
       <span v-if="task.due_date"
             class="px-2 py-1 text-xs font-semibold rounded border"
             :class="dueDateColor">
         Due: {{ formattedDueDate }}
       </span>
      
       <span v-if="task.is_blocked" class="px-2 py-1 text-xs font-semibold bg-red-100 text-red-800 rounded">Blocked</span>
     </div>
   </div>
  
   <div v-if="!task.deleted_at" class="flex gap-2 shrink-0 ml-4">
     <button v-if="task.status === 'Not Started'" @click="$emit('update-status', task.id, 'In Progress', task.version)" :disabled="task.is_blocked" class="px-3 py-1 bg-green-500 text-white rounded text-sm disabled:bg-gray-300 disabled:cursor-not-allowed">Start</button>
     <button v-if="task.status === 'In Progress'" @click="$emit('update-status', task.id, 'Completed', task.version)" class="px-3 py-1 bg-blue-500 text-white rounded text-sm">Complete</button>
     <button @click="$emit('edit', task)" class="px-3 py-1 border border-blue-500 text-blue-500 hover:bg-blue-50 rounded text-sm transition">Edit</button>
     <button @click="$emit('delete', task.id)" class="px-3 py-1 border border-red-500 text-red-500 hover:bg-red-50 rounded text-sm transition">Del</button>
   </div>
 </div>
</template>
```

- [ ] **Step 3: Commit**
Commit: `git add frontend/ && git commit -m "feat(frontend): add due date color coding and read-only state for deleted tasks"`

---

### Task 4: Vue-Native RRULE Builder Component

**Files:**
- Create: `frontend/src/components/RRuleGenerator.vue`
- Modify: `frontend/src/components/TaskFormModal.vue`

- [ ] **Step 1: Implement `RRuleGenerator.vue`**
This provides the requested user-friendly dropdowns and formats it automatically to an RFC string.
```vue
<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits(['update:modelValue'])

const frequency = ref('')
const interval = ref(1)

// Parse incoming rule
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
 if (frequency.value === 'CUSTOM') return // Leave string as-is for manual edit
  let rule = `FREQ=${frequency.value}`
 if (interval.value > 1) rule += `;INTERVAL=${interval.value}`
 emit('update:modelValue', rule)
})
</script>

<template>
 <div class="space-y-2 border p-3 rounded bg-gray-50">
   <div class="flex gap-2 items-center">
     <select v-model="frequency" class="border p-2 rounded text-sm flex-grow bg-white">
       <option value="">Does not repeat</option>
       <option value="DAILY">Daily</option>
       <option value="WEEKLY">Weekly</option>
       <option value="MONTHLY">Monthly</option>
       <option value="CUSTOM">Custom (Raw RRULE)</option>
     </select>
    
     <div v-if="frequency && frequency !== 'CUSTOM'" class="flex items-center gap-2">
       <span class="text-sm text-gray-600">Every</span>
       <input type="number" v-model="interval" min="1" class="border p-1 rounded w-16 text-sm text-center">
       <span class="text-sm text-gray-600">
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
```

- [ ] **Step 2: Integrate into `TaskFormModal.vue`**
Replace the raw RRULE input with the new component.
```vue
<script setup lang="ts">
import RRuleGenerator from './RRuleGenerator.vue'
// ... rest of script stays the same
</script>

<template>
 <div>
   <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Recurrence Schedule</label>
   <RRuleGenerator v-model="form.recurrence_rule" />
 </div>
  <div v-if="form.recurrence_rule">
   <label class="block text-xs font-bold text-gray-500 uppercase mb-1 mt-3">Calculate Next Occurrence From:</label>
   <select v-model="form.recurrence_anchor" class="w-full border p-2 rounded text-sm bg-white">
     <option value="DUE_DATE">Original Due Date</option>
     <option value="COMPLETION_DATE">Completion Date</option>
   </select>
 </div>
</template>
```

- [ ] **Step 3: Commit**
Commit: `git add frontend/ && git commit -m "feat(frontend): implement user-friendly RRuleGenerator component"`