<template>
  <div class="flex flex-col gap-2 mb-4">
    <!-- Thread header -->
    <div class="flex items-center justify-between gap-2">
      <div class="truncate font-medium text-ink-gray-8">
        {{ formattedDate }}
      </div>
      <div class="shrink-0 text-xs text-ink-gray-5">
        {{ thread.items.length }} {{ __('messages') }}
      </div>
    </div>

    <!-- Older messages toggle -->
    <div v-if="olderCount > 0" class="flex items-center">
      <Button
        variant="ghost"
        size="sm"
        class="text-ink-gray-6"
        :icon-left="expanded ? 'chevron-up' : 'chevron-down'"
        :label="`${expanded ? __('Hide previous') : __('View previous')} ${olderCount}`"
        :loading="loadingOlder"
        @click="toggleExpanded"
      />
    </div>

    <!-- Older messages list -->
    <div v-if="renderedOnce || expanded" class="flex flex-col gap-2">
      <div v-show="expanded && olderReady" class="flex flex-col gap-2">
        <div v-for="(msg, idx) in older" :key="msg.name" class="opacity-90">
          <div
            class="cursor-pointer flex flex-col rounded-md shadow px-3 py-1.5 text-base sms-bubble"
            :class="msg.data.sent_or_received === 'Sent' ? 'sms-sent' : 'sms-received'"
          >
            <div class="-mb-0.5 flex items-center justify-between gap-2">
              <div class="flex items-center gap-2 truncate text-ink-gray-9">
                <span>
                  {{ senderName(msg) }}
                </span>
              </div>
              <Tooltip :text="formatDate(msg.communication_date || msg.creation)">
                <div class="text-sm text-ink-gray-5">
                  {{ __(timeAgo(msg.communication_date || msg.creation)) }}
                </div>
              </Tooltip>
            </div>
            <div class="border-0 border-t mt-3 mb-1 border-outline-gray-modals" />
            <div class="text-ink-gray-8 whitespace-pre-wrap">{{ msg.data.content }}</div>
          </div>
          <div v-if="idx < older.length - 1" class="border-t border-outline-gray-modals my-1"></div>
        </div>
      </div>
      <div v-if="expanded && !olderReady" class="py-2 text-xs text-ink-gray-5">
        {{ __('Loading…') }}
      </div>
    </div>

    <!-- Latest message -->
    <div
      class="cursor-pointer flex flex-col rounded-md shadow px-3 py-1.5 text-base sms-bubble"
      :class="latest.data.sent_or_received === 'Sent' ? 'sms-sent' : 'sms-received'"
    >
      <div class="-mb-0.5 flex items-center justify-between gap-2">
        <div class="flex items-center gap-2 truncate text-ink-gray-9">
          <span>
            {{ senderName(latest) }}
          </span>
        </div>
        <Tooltip :text="formatDate(latest.communication_date || latest.creation)">
          <div class="text-sm text-ink-gray-5">
            {{ __(timeAgo(latest.communication_date || latest.creation)) }}
          </div>
        </Tooltip>
      </div>
      <div class="border-0 border-t mt-3 mb-1 border-outline-gray-modals" />
      <div class="text-ink-gray-8 whitespace-pre-wrap">{{ latest.data.content }}</div>
    </div>
  </div>
</template>

<script setup>
import { Button, Tooltip } from 'frappe-ui'
import { computed, ref, nextTick } from 'vue'
import { timeAgo, formatDate } from '@/utils'
import { usersStore } from '@/stores/users'

const { getUser } = usersStore()

const props = defineProps({
  thread: { type: Object, required: true },
})

const expanded = ref(false)
const loadingOlder = ref(false)
const renderedOnce = ref(false)
const olderReady = ref(false)
const older = computed(() => props.thread.items.slice(0, -1))
const latest = computed(() => props.thread.items[props.thread.items.length - 1])
const olderCount = computed(() => older.value.length)

const formattedDate = computed(() => {
  try {
    const d = new Date(props.thread.date + 'T00:00:00')
    return d.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch (_) {
    return props.thread.date
  }
})

function senderName(msg) {
  if (!msg?.data) return ''
  const full = msg.data.sender_full_name
  if (full) return full
  const u = getUser(msg.data.sender)
  return u?.full_name || msg.data.sender || __('You')
}

async function toggleExpanded() {
  const nextExpanded = !expanded.value
  const firstTimeExpanding = nextExpanded && !renderedOnce.value
  loadingOlder.value = firstTimeExpanding
  if (firstTimeExpanding) {
    renderedOnce.value = true
    olderReady.value = false
    onOlderItemLoaded._count = 0
  }
  expanded.value = nextExpanded
  await nextTick()
  if (!firstTimeExpanding) return (loadingOlder.value = false)
  setTimeout(() => {
    // In case no asynchronous loads needed (plain text), we can mark ready immediately
    if (!olderReady.value) {
      olderReady.value = true
    }
    loadingOlder.value = false
  }, 50)
}

function onOlderItemLoaded() {
  if (!olderReady.value) {
    const total = older.value.length
    onOlderItemLoaded._count = (onOlderItemLoaded._count || 0) + 1
    if (onOlderItemLoaded._count >= total) {
      olderReady.value = true
      loadingOlder.value = false
      onOlderItemLoaded._count = 0
    }
  }
}
</script>

<style scoped>
.sms-bubble.sms-sent { background-color: var(--sms-sent-bg, #eef2ff); }
.dark .sms-bubble.sms-sent { background-color: var(--sms-sent-bg-dark, rgba(99, 102, 241, 0.15)); }
.sms-bubble.sms-received { background-color: var(--sms-received-bg, var(--surface-cards, #ffffff)); }
</style>
