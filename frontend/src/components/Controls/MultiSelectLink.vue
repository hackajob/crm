<template>
  <div>
    <Autocomplete 
      :options="options" 
      :placeholder="placeholder" 
      :multiple="true" 
      v-model="selectedOptions"
      @update:modelValue="handleSelectionChange" />
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
  </div>
</template>

<script setup>
import { Autocomplete, ErrorMessage } from 'frappe-ui'
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  placeholder: {
    type: String,
    default: 'Select values...',
  },
  modelValue: {
    type: [String, Array],
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const error = ref(null)
const selectedOptions = ref([])

// Resource to fetch Link field options
const linkOptions = createResource({
  url: 'frappe.desk.search.search_link',
  params: {
    doctype: props.doctype,
    txt: '',
    page_length: 50,
  },
  auto: true,
})

const options = computed(() => {
  let linkData = linkOptions.data || []

  // Convert to option format required by Autocomplete
  return linkData.map((item) => ({
    label: item.value,
    value: item.value,
  }))
})

// Handle selection changes from Autocomplete
function handleSelectionChange(newSelection) {
  // Remove duplicates based on value
  const uniqueSelection = newSelection.filter((item, index, self) => 
    self.findIndex(t => t.value === item.value) === index
  )
  
  selectedOptions.value = uniqueSelection
  
  // For multiselect, emit an array of values (not comma-separated string)
  const arrayValue = uniqueSelection && uniqueSelection.length > 0
    ? uniqueSelection.map(opt => opt.value)
    : []
  
  emit('update:modelValue', arrayValue)
}

// Watch modelValue prop changes and update selectedOptions (only from external changes)
watch(() => props.modelValue, (newValue) => {
  let values = []
  
  if (Array.isArray(newValue) && newValue.length > 0) {
    // Handle array input
    values = newValue.filter(Boolean)
  } else if (typeof newValue === 'string' && newValue) {
    // Handle string input (comma-separated)
    values = newValue.split(',').map(v => v.trim()).filter(Boolean)
  }
  
  if (values.length > 0) {
    const newOptions = values.map(value => ({ label: value, value: value }))
    
    // Only update if different to prevent loops
    const currentValues = selectedOptions.value.map(opt => opt.value)
    const newValuesSet = new Set(values)
    const currentValuesSet = new Set(currentValues)
    
    if (newValuesSet.size !== currentValuesSet.size || 
        ![...newValuesSet].every(v => currentValuesSet.has(v))) {
      selectedOptions.value = newOptions
    }
  } else {
    selectedOptions.value = []
  }
}, { immediate: true })
</script>