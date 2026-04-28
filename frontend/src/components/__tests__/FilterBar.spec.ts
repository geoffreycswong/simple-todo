import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FilterBar from '../FilterBar.vue'

describe('FilterBar.vue', () => {
  it('emits "filter" event when status changes', async () => {
    const wrapper = mount(FilterBar)
    const statusSelect = wrapper.find('select') // First select is status
    
    await statusSelect.setValue('Completed')
    
    expect(wrapper.emitted()).toHaveProperty('filter')
    expect(wrapper.emitted('filter')![0]).toEqual([{ status: 'Completed', sort_by: 'due_date', order: 'asc' }])
  })

  it('emits "filter" event with multiple filters', async () => {
    const wrapper = mount(FilterBar)
    const selects = wrapper.findAll('select')
    const statusSelect = selects[0]
    const prioritySelect = selects[1]
    
    await statusSelect.setValue('In Progress')
    await prioritySelect.setValue('High')
    
    const emissions = wrapper.emitted('filter')
    expect(emissions).toBeDefined()
    // The last emission should have both filters plus defaults
    expect(emissions![emissions!.length - 1]).toEqual([{ status: 'In Progress', priority: 'High', sort_by: 'due_date', order: 'asc' }])
  })

  it('cleans empty strings from payload', async () => {
    const wrapper = mount(FilterBar)
    const statusSelect = wrapper.find('select')
    
    // Set to something
    await statusSelect.setValue('Completed')
    // Set back to empty
    await statusSelect.setValue('')
    
    const emissions = wrapper.emitted('filter')
    // Last emission should have only defaults
    expect(emissions![emissions!.length - 1]).toEqual([{ sort_by: 'due_date', order: 'asc' }])
  })

  it('emits "filter" event when is_deleted changes', async () => {
    const wrapper = mount(FilterBar)
    const selects = wrapper.findAll('select')
    const deletedSelect = selects[3] // 4th select
    
    await deletedSelect.setValue('true')
    
    const emissions = wrapper.emitted('filter')
    expect(emissions![emissions!.length - 1]).toEqual([{ is_deleted: 'true', sort_by: 'due_date', order: 'asc' }])
  })

  it('emits "filter" event when sort_by changes', async () => {
    const wrapper = mount(FilterBar)
    const selects = wrapper.findAll('select')
    const sortSelect = selects[4] // 5th select
    
    await sortSelect.setValue('priority')
    
    const emissions = wrapper.emitted('filter')
    expect(emissions![emissions!.length - 1]).toEqual([{ sort_by: 'priority', order: 'asc' }])
  })

  it('emits "filter" event when order changes', async () => {
    const wrapper = mount(FilterBar)
    const selects = wrapper.findAll('select')
    const orderSelect = selects[5] // 6th select
    
    await orderSelect.setValue('desc')
    
    const emissions = wrapper.emitted('filter')
    expect(emissions![emissions!.length - 1]).toEqual([{ sort_by: 'due_date', order: 'desc' }])
  })
})
