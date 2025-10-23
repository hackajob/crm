<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      onRowClick: (row) => emit('open', row.name),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    v-bind="$attrs"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader class="sm:mx-5 mx-3" @columnWidthUpdated="emit('columnWidthUpdated')">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghosted"
          class="!h-4"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>

    <ListRows class="mx-3 sm:mx-5" :rows="rows" v-slot="{ idx, column, item, row }" doctype="Communication">
      <ListRowItem :item="item" :align="column.align">
        <template #prefix>
          <div v-if="['sender','receiver'].includes(column.key)">
            <Avatar
              v-if="item?.label"
              class="flex items-center"
              :image="item.image"
              :label="item.label"
              size="sm"
            />
          </div>
          <div v-else-if="['sent_or_received'].includes(column.key)">
            <FeatherIcon :name="item.icon" class="h-3 w-3" />
          </div>
        </template>
    <template #default="{ label }">
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
            @click="
      (event) => onCellClick({ event, idx, column, item, row })
            "
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl type="checkbox" :modelValue="item" :disabled="true" class="text-ink-gray-9" />
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              v-if="column.key == '_liked_by'"
              variant="ghosted"
              :class="isLiked(item) ? 'fill-red-500' : 'fill-white'"
              @click.stop.prevent="() => emit('likeDoc', { name: row.name, liked: isLiked(item) })"
            >
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
          <div
            v-else
            class="truncate text-base"
            @click="
              (event) => onCellClick({ event, idx, column, item, row })
            "
          >
            {{ label }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>

    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown :options="listBulkActionsRef.bulkActions(selections, unselectAll)">
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    class="border-t sm:px-5 px-3 py-2"
    v-model="pageLengthCount"
    :options="{ rowCount: options.rowCount, totalCount: options.totalCount }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="Communication"
    :options="{ hideEdit: true, hideAssign: true }"
  />
</template>
<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Tooltip,
  Dropdown,
  FeatherIcon,
  FormControl,
  Button,
  Avatar,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({ selectable: true, showTooltip: true, resizeColumn: false, totalCount: 0, rowCount: 0 }),
  },
})

const emit = defineEmits([
  'open',
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const pageLengthCount = defineModel()
const list = defineModel('list')

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

defineExpose({
  customListActions: computed(() => listBulkActionsRef.value?.customListActions),
})

function onCellClick({ event, idx, column, item, row }) {
  // Remap synthetic columns to actual DB fields
  if (['sender', 'receiver'].includes(column.key)) {
    const dir = row?.sent_or_received
    let key = column.key
    let value = item?.name || item?.label || item

    if (column.key === 'receiver') {
      // Always filter by recipients for receiver
      key = 'recipients'
      value = row?.recipients || value
    } else if (column.key === 'sender') {
      // For received, sender is external number -> phone_no; for sent, it's user -> sender
      if (dir === 'Received') {
        key = 'phone_no'
        value = row?.phone_no || value
      } else {
        key = 'sender'
        value = row?.sender || value
      }
    }

    return emit('applyFilter', {
      event,
      idx,
      column: { ...column, key },
      item: { name: value, label: value },
      firstColumn: props.columns[0],
    })
  }

  // Default behavior
  emit('applyFilter', { event, idx, column, item, firstColumn: props.columns[0] })
}
</script>
