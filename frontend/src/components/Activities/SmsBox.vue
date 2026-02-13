<template>
  <div v-show="open" class="flex items-end gap-2 px-3 py-2.5 sm:px-10">
    <Textarea ref="textareaRef" type="textarea" class="min-h-8 w-full" :rows="rows" v-model="content"
      :maxlength="maxLen" :placeholder="placeholder" @focus="rows = 6" @blur="rows = 1"
      @keydown.enter.stop="(e) => send(e)" />
    <Button variant="ghost" @mousedown.prevent.stop="discard">
      {{ __('Discard') }}
    </Button>
    <Button variant="solid" :disabled="!content.trim()" @click="send()">
      {{ __('Send') }}
    </Button>
  </div>
</template>

<script setup>
import { Button, Textarea, createResource } from 'frappe-ui'
import { ref, nextTick } from 'vue'

const props = defineProps({
  doctype: String,
})

const doc = defineModel()
const emit = defineEmits(['sent', 'open', 'close'])

const rows = ref(1)
const open = ref(false)
const content = ref('')
const maxLen = 1000
const placeholder = ref(__('Type SMS here...'))
const textareaRef = ref(null)

function show() {
  open.value = true
  emit('open')
  nextTick(() => textareaRef.value.el.focus())
}

function hide() {
  emit('close')
  open.value = false
}

function discard() {
  hide()
  nextTick(() => {
    content.value = ''
    rows.value = 1
  })
}

function send(event) {
  if (event && event.shiftKey) return
  const message = content.value.trim()
  if (!message) return
  const args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    message,
    to: doc.value.mobile_no,
  }
  createResource({
    url: 'crm.api.sms.send_sms_message',
    params: args,
    auto: true,
    onSuccess: () => {
      content.value = ''
      emit('sent')
    },
  })
}

defineExpose({ show, hide })
</script>
