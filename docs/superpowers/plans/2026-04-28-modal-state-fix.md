# TODO Application: Modal State Isolation Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the "Sticky State" bug where the New Task form retains data from previous interactions.

**Architecture:** 
- **Explicit Reset Logic:** Refactor `TaskFormModal.vue` to use a dedicated reset function.
- **Open-Gate Trigger:** Force a state reset whenever the modal transitions from closed to open while in "Create" mode.

**Tech Stack:** Vue 3, Vitest.

---

### Task 1: Frontend - Form State Isolation

**Files:**
- Modify: `projects/example-todo-app/frontend/src/components/TaskFormModal.vue`
- Create: `projects/example-todo-app/frontend/src/components/__tests__/TaskFormModal.spec.ts`

- [ ] **Step 1: Write TDD test for Form Reset**
Create `TaskFormModal.spec.ts` and verify that opening the modal with `taskToEdit: null` after a previous edit session results in an empty title.
```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskFormModal from '../TaskFormModal.vue'

describe('TaskFormModal.vue State Isolation', () => {
  it('resets form to default when opening for a new task', async () => {
    const wrapper = mount(TaskFormModal, {
      props: { isOpen: true, allTasks: [], taskToEdit: { title: 'Old Task', version: 1 } }
    })
    
    // Simulate closing and reopening for a NEW task
    await wrapper.setProps({ isOpen: false })
    await wrapper.setProps({ isOpen: true, taskToEdit: null })
    
    const input = wrapper.find('input')
    expect((input.element as HTMLInputElement).value).toBe('')
  })
})
```

- [ ] **Step 2: Refactor `TaskFormModal.vue` logic**
Implement the explicit reset function and trigger it on `isOpen` change.
```typescript
const DEFAULT_FORM = {
  title: '',
  description: '',
  priority: 'Medium',
  due_date: '',
  recurrence_rule: '',
  recurrence_anchor: 'DUE_DATE',
  dependency_ids: []
}

const resetForm = () => {
  Object.assign(form, DEFAULT_FORM)
}

watch([() => props.isOpen, () => props.taskToEdit], ([newIsOpen, newTask]) => {
  if (newIsOpen) {
    if (newTask) {
      Object.assign(form, {
        ...newTask,
        due_date: newTask.due_date ? newTask.due_date.split('T')[0] : '',
        dependency_ids: newTask.dependency_ids || []
      })
    } else {
      resetForm()
    }
  }
}, { immediate: true })
```

- [ ] **Step 3: Run tests and commit**
Run: `npm run test`
Commit: `git add frontend/ && git commit -m "fix(frontend): ensure modal form state is strictly isolated between create/edit sessions"`

---

### Task 2: Final Validation

- [ ] **Step 1: Manually verify "Edit" followed by "New Task" produces a clean form.**
- [ ] **Step 2: Verify "New Task" followed by "New Task" produces a clean form.**
