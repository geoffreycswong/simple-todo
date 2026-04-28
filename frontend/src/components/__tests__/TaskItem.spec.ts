import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskItem from '../TaskItem.vue'

describe('TaskItem.vue', () => {
  const mockTask = {
    id: '1',
    title: 'Test Task',
    description: 'Test Description',
    status: 'Not Started',
    is_blocked: false,
    priority: 'Medium',
    version: 1,
    due_date: null,
    deleted_at: null
  }

  it('renders task details', () => {
    const wrapper = mount(TaskItem, {
      props: { task: mockTask }
    })

    expect(wrapper.text()).toContain('Test Task')
    expect(wrapper.text()).toContain('Not Started')
    expect(wrapper.text()).toContain('P: Medium')
  })

  it('applies red background for overdue tasks', () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    
    const wrapper = mount(TaskItem, {
      props: { 
        task: { ...mockTask, due_date: yesterday.toISOString() } 
      }
    })

    const badge = wrapper.find('[data-testid="due-date-badge"]')
    expect(badge.classes()).toContain('bg-red-100')
  })

  it('applies yellow background for tasks due today', () => {
    const today = new Date()
    
    const wrapper = mount(TaskItem, {
      props: { 
        task: { ...mockTask, due_date: today.toISOString() } 
      }
    })

    const badge = wrapper.find('[data-testid="due-date-badge"]')
    expect(badge.classes()).toContain('bg-yellow-100')
  })

  it('hides action buttons when task is deleted', () => {
    const wrapper = mount(TaskItem, {
      props: { 
        task: { ...mockTask, deleted_at: new Date().toISOString() } 
      }
    })

    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.text()).toContain('Deleted')
  })

  it('emits update-status when Start is clicked', async () => {
    const wrapper = mount(TaskItem, {
      props: { task: mockTask }
    })

    const startBtn = wrapper.find('button')
    expect(startBtn.text()).toBe('Start')
    await startBtn.trigger('click')

    expect(wrapper.emitted('update-status')).toBeTruthy()
    expect(wrapper.emitted('update-status')![0]).toEqual(['1', 'In Progress', 1])
  })
})
