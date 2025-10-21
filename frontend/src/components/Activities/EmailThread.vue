<template>
  <div class="flex flex-col gap-2 mb-4">
    <!-- Thread header -->
    <div class="flex items-center justify-between gap-2">
      <div class="truncate font-medium text-ink-gray-8">
        {{ thread.subject || __('(no subject)') }}
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
          <EmailArea :activity="msg" :emailBox="emailBox" :hide-subject="true" :visible="expanded" @loaded="onOlderItemLoaded" />
          <div v-if="idx < older.length - 1" class="border-t border-outline-gray-modals my-1"></div>
        </div>
      </div>
      <div v-if="expanded && !olderReady" class="py-2 text-xs text-ink-gray-5">
        {{ __('Loading…') }}
      </div>
    </div>

    <!-- Latest message -->
    <EmailArea :activity="latest" :emailBox="emailBox" :hide-subject="true" />
  </div>

</template>

<script setup>
import EmailArea from '@/components/Activities/EmailArea.vue'
import { computed, ref, nextTick } from 'vue'

const props = defineProps({
  thread: { type: Object, required: true },
  emailBox: { type: Object, required: true },
})

const expanded = ref(false)
const loadingOlder = ref(false)
const renderedOnce = ref(false)
const olderReady = ref(false)

const older = computed(() => props.thread.items.slice(0, -1))
const latest = computed(() => props.thread.items[props.thread.items.length - 1])
const olderCount = computed(() => older.value.length)

async function toggleExpanded() {
  const nextExpanded = !expanded.value
  const firstTimeExpanding = nextExpanded && !renderedOnce.value
  // Only show spinner on the first expand
  loadingOlder.value = firstTimeExpanding

  if (firstTimeExpanding) {
    renderedOnce.value = true
    olderReady.value = false
  onOlderItemLoaded._count = 0
  }
  expanded.value = nextExpanded

  await nextTick()
  if (!firstTimeExpanding) return (loadingOlder.value = false)

  // Small delay to allow EmailContent iframe onload to compute height
  setTimeout(() => {
    loadingOlder.value = false
  }, 150)
}

function onOlderItemLoaded() {
  // When all older items report loaded, mark ready
  // Using counts avoids race conditions
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

<style scoped></style>
