import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskFormModal from '../TaskFormModal.vue'

describe('TaskFormModal.vue', () => {
  const allTasks = [
    { id: '1', title: 'Task 1' },
    { id: '2', title: 'Task 2' }
  ]

  it('renders "New Task" title when taskToEdit is null', () => {
    const wrapper = mount(TaskFormModal, {
      props: {
        isOpen: true,
        allTasks: allTasks,
        taskToEdit: null
      }
    })

    expect(wrapper.find('h2').text()).toBe('New Task')
  })

  it('renders "Edit Task" title and pre-fills form when taskToEdit is provided', () => {
    const taskToEdit = {
      id: '3',
      title: 'Existing Task',
      description: 'Existing Description',
      priority: 'High',
      due_date: '2026-12-31T00:00:00.000Z',
      recurrence_rule: 'FREQ=DAILY',
      recurrence_anchor: 'COMPLETION_DATE',
      dependency_ids: ['1'],
      version: 5
    }

    const wrapper = mount(TaskFormModal, {
      props: {
        isOpen: true,
        allTasks: allTasks,
        taskToEdit: taskToEdit
      }
    })

    expect(wrapper.find('h2').text()).toBe('Edit Task')
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('Existing Task')
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('Existing Description')
    expect((wrapper.find('select').element as HTMLSelectElement).value).toBe('High')
    // Date input should be YYYY-MM-DD
    const dateInput = wrapper.findAll('input').find(i => i.attributes('type') === 'date')
    expect((dateInput?.element as HTMLInputElement).value).toBe('2026-12-31')
  })

  it('emits submit with correct payload when Save is clicked', async () => {
    const taskToEdit = {
      id: '3',
      title: 'Existing Task',
      version: 1
    }

    const wrapper = mount(TaskFormModal, {
      props: {
        isOpen: true,
        allTasks: allTasks,
        taskToEdit: taskToEdit
      }
    })

    await wrapper.find('button.bg-blue-600').trigger('click')

    expect(wrapper.emitted('submit')).toBeTruthy()
    const payload = wrapper.emitted('submit')![0][0] as any
    expect(payload.title).toBe('Existing Task')
    expect(payload.version).toBe(1)
  })

  it('emits close when Cancel is clicked', async () => {
    const wrapper = mount(TaskFormModal, {
      props: {
        isOpen: true,
        allTasks: [],
        taskToEdit: null
      }
    })

    const cancelButton = wrapper.findAll('button').find(b => b.text() === 'Cancel')
    await cancelButton?.trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
