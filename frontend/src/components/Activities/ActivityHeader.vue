<template>
  <div v-if="title !== 'Data'"
    class="mx-4 my-3 flex items-center justify-between text-lg font-medium sm:mx-10 sm:mb-4 sm:mt-8">
    <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
      {{ __(title) }}
    </div>
    <Button v-if="title == 'Emails'" variant="solid" :label="__('New Email')" iconLeft="plus"
      @click="emailBox.show = true" />
    <Button v-else-if="title == 'Comments'" variant="solid" :label="__('New Comment')" iconLeft="plus"
      @click="emailBox.showComment = true" />
    <MultiActionButton v-else-if="title == 'Calls'" variant="solid" :options="callActions" />
    <Button v-else-if="title == 'Notes'" variant="solid" :label="__('New Note')" iconLeft="plus"
      @click="modalRef.showNote()" />
    <Button v-else-if="title == 'Tasks'" variant="solid" :label="__('New Task')" iconLeft="plus"
      @click="modalRef.showTask()" />
    <Button v-else-if="title == 'Attachments'" variant="solid" :label="__('Upload Attachment')" iconLeft="plus"
      @click="showFilesUploader = true" />
    <div class="flex gap-2 shrink-0" v-else-if="title == 'WhatsApp'">
      <Button :label="__('Send Template')" @click="showWhatsappTemplates = true" />
      <Button variant="solid" :label="__('New Message')" iconLeft="plus" @click="whatsappBox.show()" />
    </div>
    <Button v-else-if="title == 'SMS'" variant="solid" @click="openSms()">
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ __('New SMS') }}</span>
    </Button>
    <Dropdown v-else :options="defaultActions" @click.stop>
      <template v-slot="{ open }">
        <Button variant="solid" class="flex items-center gap-1" :label="__('New')" iconLeft="plus"
          :iconRight="open ? 'chevron-up' : 'chevron-down'" />
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import MultiActionButton from '@/components/MultiActionButton.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import SmsIcon from '@/components/Icons/SmsIcon.vue'
import { globalStore } from '@/stores/global'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import { Dropdown, toast } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  tabs: Array,
  title: String,
  doc: Object,
  modalRef: Object,
  emailBox: Object,
  whatsappBox: Object,
  smsBox: Object,
})

const { makeCall } = globalStore()

const tabIndex = defineModel()
const showWhatsappTemplates = defineModel('showWhatsappTemplates')
const showFilesUploader = defineModel('showFilesUploader')

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(Email2Icon, { class: 'h-4 w-4' }),
      label: __('New Email'),
      onClick: () => (props.emailBox.show = true),
    },
    {
      icon: h(SmsIcon, { class: 'h-4 w-4' }),
      label: __('New SMS'),
      onClick: () => openSms(true),
      condition: () => !!props.doc?.mobile_no,
    },
    {
      icon: h(CommentIcon, { class: 'h-4 w-4' }),
      label: __('New Comment'),
      onClick: () => (props.emailBox.showComment = true),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Log a Call'),
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => props.modalRef.showNote(),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => props.modalRef.showTask(),
    },
    {
      icon: h(AttachmentIcon, { class: 'h-4 w-4' }),
      label: __('Upload Attachment'),
      onClick: () => (showFilesUploader.value = true),
    },
    {
      icon: h(WhatsAppIcon, { class: 'h-4 w-4' }),
      label: __('New WhatsApp Message'),
      onClick: () => (tabIndex.value = getTabIndex('WhatsApp')),
      condition: () => whatsappEnabled.value,
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})

function getTabIndex(name) {
  return props.tabs.findIndex((tab) => tab.name === name)
}

function openSms(fromDropdown = false) {
  if (!props.doc?.mobile_no) return toast.error(__('No phone number set'))
  // If already on Activity, open SMS box in-place; otherwise, switch to SMS tab
  if (props.title === 'Activity' && !fromDropdown) {
    return setTimeout(() => props.smsBox?.show?.(), 0)
  }
  if (props.title === 'Activity' && fromDropdown) {
    // From the New dropdown on Activity, still show in-place
    return setTimeout(() => props.smsBox?.show?.(), 0)
  }
  // If current header is SMS tab, simply show
  if (props.title === 'SMS') return setTimeout(() => props.smsBox?.show?.(), 0)
  // Otherwise, navigate to SMS tab and open
  tabIndex.value = getTabIndex('SMS')
  setTimeout(() => props.smsBox?.show?.(), 0)
}

const callActions = computed(() => {
  let actions = [
    {
      label: __('Log a Call'),
      icon: 'plus',
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      label: __('Make a Call'),
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
  ]

  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})
</script>
