<template>
  <div class="whitespace-nowrap overflow-hidden">
    <Autocomplete
      class="w-full whitespace-nowrap overflow-hidden text-ellipsis"
      :options="computedOptions"
      :placeholder="placeholder"
      :multiple="true"
      v-model="selectedOptions"
      @update:modelValue="handleSelectionChange"
    />
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
  </div>
</template>

<script setup>
import { Autocomplete, ErrorMessage } from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const props = defineProps({
  // Array of strings or array of { label, value }
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Select values...',
  },
  modelValue: {
    type: [String, Array],
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue'])

const error = ref(null)
const selectedOptions = ref([])

const computedOptions = computed(() => {
  // Normalize options to { label, value }
  return (props.options || []).map((opt) => {
    if (typeof opt === 'string') {
      return { label: opt, value: opt }
    }
    if (opt && typeof opt === 'object') {
      return { label: opt.label ?? opt.value, value: opt.value ?? opt.label }
    }
    return { label: String(opt), value: String(opt) }
  })
})

function handleSelectionChange(newSelection) {
  // De-duplicate by value
  const unique = newSelection.filter(
    (item, idx, self) => self.findIndex((t) => t.value === item.value) === idx,
  )

  selectedOptions.value = unique

  const arrayValue = unique.length ? unique.map((o) => o.value) : []
  emit('update:modelValue', arrayValue)
}

// Sync external modelValue into internal selectedOptions
watch(
  () => props.modelValue,
  (newValue) => {
    let values = []
    if (Array.isArray(newValue)) {
      values = newValue.filter(Boolean)
    } else if (typeof newValue === 'string' && newValue) {
      values = newValue
        .split(',')
        .map((v) => v.trim())
        .filter(Boolean)
    }

    const asOptions = values.map((v) => ({ label: v, value: v }))
    const current = selectedOptions.value.map((o) => o.value)
    const nv = new Set(values)
    const cv = new Set(current)
    if (
      nv.size !== cv.size ||
      [...nv].some((v) => !cv.has(v))
    ) {
      selectedOptions.value = asOptions
    }
    if (values.length === 0) {
      selectedOptions.value = []
    }
  },
  { immediate: true },
)
</script>
