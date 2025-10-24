<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="SMS Logs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="smsLogsListView?.customListActions"
        :actions="smsLogsListView.customListActions"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="smsLogs"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Communication"
    :filters="defaultFilters"
    :options="{ allowedViews: ['list','group_by'] }"
  />
  <SmsLogsListView
    ref="smsLogsListView"
    v-if="smsLogs.data && rows.length"
    v-model="smsLogs.data.page_length_count"
    v-model:list="smsLogs"
    :rows="rows"
    :columns="smsLogs.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: smsLogs.data.row_count,
      totalCount: smsLogs.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  @open="openDetail"
  />
  <div
    v-else-if="smsLogs.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <SmsIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Logs')]) }}</span>
    </div>
  </div>
  <SmsLogDetailModal
    v-model="showDetailModal"
    v-model:log="activeLog"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import SmsIcon from '@/components/Icons/SmsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import SmsLogsListView from '@/components/ListViews/SmsLogsListView.vue'
import SmsLogDetailModal from '@/components/Modals/SmsLogDetailModal.vue'
import { getSmsLogDetail } from '@/utils/smsLog'
import { computed, ref, onMounted, watch } from 'vue'
import { call } from 'frappe-ui'

const smsLogsListView = ref(null)

// list data is loaded in the ViewControls component
const smsLogs = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const defaultFilters = {
  communication_type: 'Communication',
  communication_medium: 'SMS',
}

// After first load, if default columns/rows are not ideal, set reasonable defaults
watch(
  () => smsLogs.value?.data?.columns,
  (cols) => {
    if (!smsLogs.value?.data || cols === undefined || cols === null) return
    const isEmpty = Array.isArray(cols) && cols.length === 0
    const isFallback = Array.isArray(cols)
      && cols.length <= 2
      && cols.map((c) => c.key).includes('name')
      && cols.map((c) => c.key).includes('modified')

  if (isEmpty || isFallback) {
      smsLogs.value.params.columns = [
        { label: 'Sender', type: 'Data', key: 'sender', width: '12rem' },
        { label: 'Receiver', type: 'Data', key: 'receiver', width: '12rem' },
        { label: 'From', type: 'Data', key: 'phone_no', width: '12rem' },
        { label: 'To', type: 'Data', key: 'recipients', width: '12rem' },
        { label: 'Message', type: 'Text', key: 'content', width: '1fr' },
        { label: 'Direction', type: 'Data', key: 'sent_or_received', width: '8rem' },
        { label: 'When', type: 'Datetime', key: 'creation', width: '10rem' },
      ]
      smsLogs.value.params.rows = [
    'name',
        'creation',
        'sent_or_received',
    'sender',
    'receiver',
        'phone_no',
        'recipients',
        'content',
        'reference_doctype',
        'reference_name',
        '_liked_by',
      ]
      // Optionally increase page size for better first paint
      smsLogs.value.params.page_length = smsLogs.value.params.page_length || 50
      smsLogs.value.params.page_length_count = smsLogs.value.params.page_length_count || 50
      smsLogs.value.reload()
    }
  },
  { immediate: false },
)

const rows = computed(() => {
  if (
    !smsLogs.value?.data?.data ||
    !['list', 'group_by'].includes(smsLogs.value.data.view_type)
  )
    return []
  return smsLogs.value?.data.data.map((log) => {
    let _rows = {}
    smsLogs.value?.data.rows.forEach((row) => {
      _rows[row] = getSmsLogDetail(row, log, smsLogs.value?.data.columns)
    })
    // Replace From (phone_no) with agent number when Sent, if known
    if (
      log.sent_or_received === 'Sent' &&
      agentNumbers.value &&
      log.sender &&
      agentNumbers.value[log.sender]
    ) {
      _rows['phone_no'] = agentNumbers.value[log.sender]
    }

    // For Received, resolve receiver (agent) from recipients -> CRM Telephony Agent.twilio_number
    if (log.sent_or_received === 'Received') {
      const toNumber = parseFirstRecipientNumber(log?.recipients)
      if (toNumber && agentByNumbers.value?.[toNumber]) {
        const info = agentByNumbers.value[toNumber]
        _rows['receiver'] = {
          label: info?.full_name || info?.user || 'Unknown',
          image: info?.user_image || null,
        }
      }
    }
    return _rows
  })
})

const showDetailModal = ref(false)
const activeLog = defineModel('log', { default: {} })

function openDetail(name) {
  const rec = (smsLogs.value?.data?.data || []).find((d) => d.name === name)
  if (rec) {
    activeLog.value = { data: rec }
    showDetailModal.value = true
  }
}

// open detail from URL if needed (?open=<name>)
function openFromURL() {
  const searchParams = new URLSearchParams(window.location.search)
  const name = searchParams.get('open')
  if (name) {
    const rec = (smsLogs.value?.data?.data || []).find((d) => d.name === name)
    if (rec) {
      activeLog.value = { data: rec }
      showDetailModal.value = true
    }
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}

onMounted(() => {
  // Ensure first load has proper columns/rows so server returns records
  const primeColumns = () => {
    const p = smsLogs.value?.params
    if (!p) return setTimeout(primeColumns, 10)
    const noCols = !Array.isArray(p.columns) || p.columns.length === 0
  if (noCols) {
      p.columns = [
        { label: 'Sender', type: 'Data', key: 'sender', width: '12rem' },
        { label: 'Receiver', type: 'Data', key: 'receiver', width: '12rem' },
        { label: 'From', type: 'Data', key: 'phone_no', width: '12rem' },
        { label: 'To', type: 'Data', key: 'recipients', width: '12rem' },
        { label: 'Message', type: 'Text', key: 'content', width: '1fr' },
        { label: 'Direction', type: 'Data', key: 'sent_or_received', width: '8rem' },
        { label: 'When', type: 'Datetime', key: 'creation', width: '10rem' },
      ]
      p.rows = [
        'name',
        'creation',
        'sent_or_received',
    'sender',
    'receiver',
        'phone_no',
        'recipients',
        'content',
        'reference_doctype',
        'reference_name',
        '_liked_by',
      ]
      p.page_length = p.page_length || 50
      p.page_length_count = p.page_length_count || 50
      smsLogs.value.reload()
    }
  }
  primeColumns()
  openFromURL()
})

// Fetch agent numbers for unique senders on the page (for Sent rows)
const agentNumbers = ref({})
// Fetch agent info by our Twilio numbers (for Received rows)
const agentByNumbers = ref({})
function parseFirstRecipientNumber(val) {
  if (!val) return ''
  // recipients can be a single number or comma/space separated; take first token
  if (Array.isArray(val)) return String(val[0] || '')
  const s = String(val)
  const token = s.split(',')[0].trim().split(' ')[0].trim()
  return token
}
watch(
  () => smsLogs.value?.data?.data,
  async (list) => {
    if (!Array.isArray(list) || list.length === 0) return
    const senders = Array.from(
      new Set(
        list
          .filter((d) => d.sent_or_received === 'Sent' && !!d.sender)
          .map((d) => d.sender),
      ),
    )
    const missing = senders.filter((u) => !(u in agentNumbers.value))
    if (!missing.length) return
    try {
      const res = await call('crm.api.sms.get_agent_numbers', { users: missing })
      agentNumbers.value = { ...agentNumbers.value, ...(res || {}) }
    } catch (e) {
      // ignore
    }
  },
  { immediate: true },
)

// Watch and fetch agents by their Twilio (To) numbers for Received rows
watch(
  () => smsLogs.value?.data?.data,
  async (list) => {
    if (!Array.isArray(list) || list.length === 0) return
    const numbers = Array.from(
      new Set(
        list
          .filter((d) => d.sent_or_received === 'Received' && !!d.recipients)
          .map((d) => parseFirstRecipientNumber(d.recipients))
          .filter(Boolean),
      ),
    )
    const missing = numbers.filter((n) => !(n in agentByNumbers.value))
    if (!missing.length) return
    try {
      const res = await call('crm.api.sms.get_agents_by_numbers', { numbers: missing })
      agentByNumbers.value = { ...agentByNumbers.value, ...(res || {}) }
    } catch (e) {
      // ignore
    }
  },
  { immediate: true },
)
</script>
