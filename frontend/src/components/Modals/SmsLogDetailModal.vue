<template>
  <Dialog v-model="show">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('SMS Details') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button icon="x" variant="ghost" class="w-7" @click="show = false" />
          </div>
        </div>
        <div class="flex flex-col gap-3.5">
          <div class="flex gap-2 text-base text-ink-gray-8">
            <div class="grid size-7 place-content-center">
              <component :is="directionIcon" />
            </div>
            <div class="flex min-h-7 w-full items-center gap-2">
              <div>
                <div class="text-sm text-ink-gray-6">{{ __('Direction') }}</div>
                <div class="font-medium">{{ directionLabel }}</div>
              </div>
            </div>
          </div>
          <div class="flex gap-2 text-base text-ink-gray-8">
            <div class="grid size-7 place-content-center">
              <FeatherIcon name="user" class="h-4 w-4" />
            </div>
            <div class="flex min-h-7 w-full items-center gap-2">
              <div>
                <div class="text-sm text-ink-gray-6">{{ __('From') }}</div>
                <div class="font-medium">{{ fromNumber || log.data?.phone_no || '-' }}</div>
              </div>
              <FeatherIcon name="arrow-right" class="mx-2 h-4 w-4 text-ink-gray-5" />
              <div>
                <div class="text-sm text-ink-gray-6">{{ __('To') }}</div>
                <div class="font-medium">{{ log.data?.recipients || '-' }}</div>
              </div>
            </div>
          </div>
          <div class="flex gap-2 text-base text-ink-gray-8">
            <div class="grid size-7 place-content-center">
              <FeatherIcon name="calendar" class="h-4 w-4" />
            </div>
            <div class="flex min-h-7 w-full items-center gap-2">
              <Tooltip :text="formattedDateFull">
                {{ formattedDateFull }}
              </Tooltip>
            </div>
          </div>
          <div class="flex gap-2 text-base text-ink-gray-8">
            <div class="grid size-7 place-content-center">
              <FeatherIcon name="message-circle" class="h-4 w-4" />
            </div>
            <div class="w-full rounded border px-2 pt-1.5 text-base text-ink-gray-7">
              <div class="whitespace-pre-wrap">{{ log.data?.content }}</div>
            </div>
          </div>
          <div v-if="log.data?.reference_doctype && log.data?.reference_name" class="flex gap-2 text-base text-ink-gray-8">
            <div class="grid size-7 place-content-center">
              <FeatherIcon name="link" class="h-4 w-4" />
            </div>
            <div class="flex min-h-7 w-full items-center gap-2">
              <div>
                <div class="text-sm text-ink-gray-6">{{ __('Linked To') }}</div>
                <div class="font-medium">{{ log.data?.reference_doctype }} / {{ log.data?.reference_name }}</div>
              </div>
              <ArrowUpRightIcon
                class="h-4 w-4 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
                @click="openReference"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import InboundSmsIcon from '@/components/Icons/InboundSmsIcon.vue'
import OutboundSmsIcon from '@/components/Icons/OutboundSmsIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import { Tooltip, FeatherIcon, Button, call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { formatDate } from '@/utils'

const show = defineModel()
const log = defineModel('log', { default: {} })
const router = useRouter()

const directionIcon = computed(() =>
  (log.value?.data?.sent_or_received || '') === 'Sent' ? OutboundSmsIcon : InboundSmsIcon,
)
const directionLabel = computed(() =>
  (log.value?.data?.sent_or_received || '') === 'Sent' ? __('Sent') : __('Received'),
)
const formattedDateFull = computed(() => {
  const ts = log.value?.data?.communication_date || log.value?.data?.creation
  return ts ? formatDate(ts) : '-'
})

// Show agent number for Sent SMS in From field
const fromNumber = ref('')
async function refreshFromNumber() {
  const d = log.value?.data
  fromNumber.value = ''
  if (!d) return
  if (d.sent_or_received === 'Sent' && d.sender) {
    try {
      const res = await call('crm.api.sms.get_agent_numbers', { users: [d.sender] })
      fromNumber.value = res?.[d.sender] || ''
    } catch (_) {
      fromNumber.value = ''
    }
  } else {
    // For received, prefer phone_no; template fallback covers this
    fromNumber.value = ''
  }
}

watch(
  () => [log.value?.data?.name, log.value?.data?.sender, log.value?.data?.sent_or_received],
  () => refreshFromNumber(),
  { immediate: true },
)

function openReference() {
  const d = log.value?.data
  if (!d?.reference_doctype || !d?.reference_name) return
  if (d.reference_doctype === 'CRM Lead') {
    router.push({ name: 'Lead', params: { leadId: d.reference_name } })
  } else if (d.reference_doctype === 'CRM Deal') {
    router.push({ name: 'Deal', params: { dealId: d.reference_name } })
  }
}
</script>
