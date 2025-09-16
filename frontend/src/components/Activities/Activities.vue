<template>
  <ActivityHeader
    v-model="tabIndex"
    v-model:showWhatsappTemplates="showWhatsappTemplates"
    v-model:showFilesUploader="showFilesUploader"
    :tabs="tabs"
    :title="title"
    :doc="doc"
    :emailBox="emailBox"
    :whatsappBox="whatsappBox"
    :smsBox="smsBox"
    :modalRef="modalRef"
  />
  <FadedScrollableDiv
    :maskHeight="30"
    class="flex flex-col flex-1 overflow-y-auto"
  >
    <div
      v-if="all_activities?.loading"
      class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>
    <div
      v-else-if="
        activities?.length ||
        (whatsappMessages.data?.length && title == 'WhatsApp')
      "
      class="activities"
    >
      <div v-if="title == 'WhatsApp' && whatsappMessages.data?.length">
        <WhatsAppArea
          class="px-3 sm:px-10"
          v-model="whatsappMessages"
          v-model:reply="replyMessage"
          :messages="whatsappMessages.data"
        />
      </div>
      <div
        v-else-if="title == 'Notes'"
        class="grid grid-cols-1 gap-4 px-3 pb-3 sm:px-10 sm:pb-5 lg:grid-cols-2 xl:grid-cols-3"
      >
        <div v-for="note in activities" @click="modalRef.showNote(note)">
          <NoteArea :note="note" v-model="all_activities" />
        </div>
      </div>
      <div v-else-if="title == 'Comments'" class="pb-5">
        <div v-for="(comment, i) in activities">
          <div
            class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 px-3 sm:gap-4 sm:px-10"
          >
            <div
              class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
              :class="
                i != activities.length - 1 ? 'before:h-full' : 'before:h-4'
              "
            >
              <div
                class="flex h-8 w-7 items-center justify-center bg-surface-white"
              >
                <CommentIcon class="text-ink-gray-8" />
              </div>
            </div>
            <CommentArea class="mb-4" :activity="comment" />
          </div>
        </div>
      </div>
      <div v-else-if="title == 'Tasks'" class="px-3 pb-3 sm:px-10 sm:pb-5">
        <TaskArea :modalRef="modalRef" :tasks="activities" :doctype="doctype" />
      </div>
      <div v-else-if="title == 'Calls'" class="activity">
        <div v-for="(call, i) in activities">
          <div
            class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-3 sm:px-10"
          >
            <div
              class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
              :class="
                i != activities.length - 1 ? 'before:h-full' : 'before:h-4'
              "
            >
              <div
                class="flex h-8 w-7 items-center justify-center bg-surface-white text-ink-gray-8"
              >
                <MissedCallIcon
                  v-if="call.status == 'No Answer'"
                  class="text-ink-red-4"
                />
                <DeclinedCallIcon v-else-if="call.status == 'Busy'" />
                <component
                  v-else
                  :is="
                    call.type == 'Incoming' ? InboundCallIcon : OutboundCallIcon
                  "
                />
              </div>
            </div>
            <CallArea class="mb-4" :activity="call" />
          </div>
        </div>
      </div>
      <div
        v-else-if="title == 'Attachments'"
        class="px-3 pb-3 sm:px-10 sm:pb-5"
      >
        <AttachmentArea
          :attachments="activities"
          @reload="all_activities.reload() && scroll()"
        />
      </div>
  <!-- Emails threaded view (Emails tab only) -->
      <div v-else-if="title == 'Emails'" class="px-3 sm:px-10">
        <div v-for="thread in emailThreads" :key="thread.subject" class="activity">
          <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4">
            <div class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-outline-gray-modals before:h-full">
              <div class="z-10 flex h-8 w-7 items-center justify-center bg-surface-white">
                <UserAvatar :user="thread.items[thread.items.length - 1].data.sender" size="md" />
              </div>
            </div>
            <div class="pb-5 mt-px w-full">
              <EmailThread :thread="thread" :emailBox="emailBox" />
            </div>
          </div>
        </div>
      </div>
  <!-- SMS threaded view (SMS tab only) -->
      <div v-else-if="title == 'SMS'" class="px-3 sm:px-10">
        <div v-for="thread in smsThreads" :key="thread.date" class="activity">
          <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4">
            <div class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-outline-gray-modals before:h-full">
              <div class="z-10 flex h-8 w-7 items-center justify-center bg-surface-white">
                <UserAvatar :user="thread.items[thread.items.length - 1].data.sender" size="md" />
              </div>
            </div>
            <div class="pb-5 mt-px w-full">
              <SmsThread :thread="thread" />
            </div>
          </div>
        </div>
      </div>
      <!-- Activity tab unified timeline (threads + calls + notes + other activities chronologically) -->
      <div v-else-if="title == 'Activity'" class="px-3 sm:px-10">
        <div
          v-for="(item, i) in activityTimeline"
          :key="item.key"
          class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4"
        >
          <div
            class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:border-l before:border-outline-gray-modals"
            :class="i != activityTimeline.length - 1 ? 'before:h-full' : 'before:h-4'"
          >
            <div
              v-if="item.kind === 'email_thread' || item.kind === 'sms_thread'"
              class="z-10 flex h-8 w-7 items-center justify-center bg-surface-white"
            >
              <UserAvatar :user="item.thread.items[item.thread.items.length - 1].data.sender" size="md" />
            </div>
            <div
              v-else-if="item.kind === 'note'"
              class="z-10 flex h-8 w-7 items-center justify-center bg-surface-white"
            >
              <UserAvatar :user="item.note.owner" size="md" />
            </div>
            <div
              v-else
              class="flex h-7 w-7 items-center justify-center bg-surface-white"
              :class="{
                'mt-2.5': ['communication'].includes(item.activity.activity_type),
                'bg-surface-white': ['added','removed','changed'].includes(item.activity.activity_type),
                'h-8': ['comment','communication','incoming_call','outgoing_call'].includes(item.activity.activity_type),
              }"
            >
              <UserAvatar
                v-if="item.activity.activity_type == 'communication'"
                :user="item.activity.data.sender"
                size="md"
              />
              <MissedCallIcon
                v-else-if="['incoming_call','outgoing_call'].includes(item.activity.activity_type) && item.activity.status == 'No Answer'"
                class="text-ink-red-4"
              />
              <DeclinedCallIcon
                v-else-if="['incoming_call','outgoing_call'].includes(item.activity.activity_type) && item.activity.status == 'Busy'"
              />
              <component
                v-else
                :is="item.activity.icon"
                :class="['added','removed','changed'].includes(item.activity.activity_type) ? 'text-ink-gray-4' : 'text-ink-gray-8'"
              />
            </div>
          </div>
          <!-- Thread bodies -->
          <div v-if="item.kind === 'email_thread'" class="pb-5 mt-px w-full">
            <EmailThread :thread="item.thread" :emailBox="emailBox" />
          </div>
          <div v-else-if="item.kind === 'sms_thread'" class="pb-5 mt-px w-full">
            <SmsThread :thread="item.thread" />
          </div>
          <div v-else-if="item.kind === 'note'" class="pb-5 mt-px w-full cursor-pointer" @click="modalRef.showNote(item.note)">
            <NoteArea :note="item.note" v-model="all_activities" />
          </div>
          <!-- Activity types -->
          <template v-else>
            <!-- Call log -->
            <div
              v-if="['incoming_call','outgoing_call'].includes(item.activity.activity_type)"
              class="mb-4 mt-px"
            >
              <CallArea :activity="item.activity" />
            </div>
            <!-- Comment -->
            <div v-else-if="item.activity.activity_type == 'comment'" class="pb-5 mt-px">
              <CommentArea :activity="item.activity" />
            </div>
            <!-- Attachment log -->
            <div
              v-else-if="item.activity.activity_type == 'attachment_log'"
              class="mb-4 flex flex-col gap-2 py-1.5"
            >
              <div class="flex items-center justify-stretch gap-2 text-base">
                <div class="inline-flex items-center flex-wrap gap-1.5 text-ink-gray-8 font-medium">
                  <span class="font-medium">{{ item.activity.owner_name }}</span>
                  <span class="text-ink-gray-5">{{ __(item.activity.data.type) }}</span>
                  <a
                    v-if="item.activity.data.file_url"
                    :href="item.activity.data.file_url"
                    target="_blank"
                  >
                    <span>{{ item.activity.data.file_name }}</span>
                  </a>
                  <span v-else>{{ item.activity.data.file_name }}</span>
                  <FeatherIcon
                    v-if="item.activity.data.is_private"
                    name="lock"
                    class="size-3"
                  />
                </div>
                <div class="ml-auto whitespace-nowrap">
                  <Tooltip :text="formatDate(item.activity.creation)">
                    <div class="text-sm text-ink-gray-5">
                      {{ __(timeAgo(item.activity.creation)) }}
                    </div>
                  </Tooltip>
                </div>
              </div>
            </div>
            <!-- Generic changes -->
            <div v-else class="mb-4 flex flex-col gap-2 py-1.5">
              <div class="flex items-center justify-stretch gap-2 text-base">
                <div
                  v-if="item.activity.other_versions"
                  class="inline-flex flex-wrap gap-1.5 text-ink-gray-8 font-medium"
                >
                  <span>{{ item.activity.show_others ? __('Hide') : __('Show') }}</span>
                  <span> +{{ item.activity.other_versions.length + 1 }} </span>
                  <span>{{ __('changes from') }}</span>
                  <span>{{ item.activity.owner_name }}</span>
                  <Button
                    class="!size-4"
                    variant="ghost"
                    :icon="SelectIcon"
                    @click="item.activity.show_others = !item.activity.show_others"
                  />
                </div>
                <div
                  v-else
                  class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5"
                >
                  <span class="font-medium text-ink-gray-8">
                    {{ item.activity.owner_name }}
                  </span>
                  <span v-if="item.activity.type">{{ __(item.activity.type) }}</span>
                  <span
                    v-if="item.activity.data?.field_label"
                    class="max-w-xs truncate font-medium text-ink-gray-8"
                  >
                    {{ __(item.activity.data.field_label) }}
                  </span>
                  <span v-if="item.activity.value">{{ __(item.activity.value) }}</span>
                  <span
                    v-if="item.activity.data?.old_value"
                    class="max-w-xs font-medium text-ink-gray-8"
                  >
                    <div
                      class="flex items-center gap-1"
                      v-if="item.activity.options == 'User'"
                    >
                      <UserAvatar :user="item.activity.data.old_value" size="xs" />
                      {{ getUser(item.activity.data.old_value).full_name }}
                    </div>
                    <div class="truncate" v-else>
                      {{ item.activity.data.old_value }}
                    </div>
                  </span>
                  <span v-if="item.activity.to">{{ __('to') }}</span>
                  <span
                    v-if="item.activity.data?.value"
                    class="max-w-xs font-medium text-ink-gray-8"
                  >
                    <div
                      class="flex items-center gap-1"
                      v-if="item.activity.options == 'User'"
                    >
                      <UserAvatar :user="item.activity.data.value" size="xs" />
                      {{ getUser(item.activity.data.value).full_name }}
                    </div>
                    <div class="truncate" v-else>
                      {{ item.activity.data.value }}
                    </div>
                  </span>
                </div>

                <div class="ml-auto whitespace-nowrap">
                  <Tooltip :text="formatDate(item.activity.creation)">
                    <div class="text-sm text-ink-gray-5">
                      {{ __(timeAgo(item.activity.creation)) }}
                    </div>
                  </Tooltip>
                </div>
              </div>
              <div
                v-if="item.activity.other_versions && item.activity.show_others"
                class="flex flex-col gap-0.5"
              >
                <div
                  v-for="activity in [item.activity, ...item.activity.other_versions]"
                  class="flex items-start justify-stretch gap-2 py-1.5 text-base"
                >
                  <div class="inline-flex flex-wrap gap-1 text-ink-gray-5">
                    <span
                      v-if="activity.data?.field_label"
                      class="max-w-xs truncate text-ink-gray-5"
                    >
                      {{ __(activity.data.field_label) }}
                    </span>
                    <FeatherIcon
                      name="arrow-right"
                      class="mx-1 h-4 w-4 text-ink-gray-5"
                    />
                    <span v-if="activity.type">
                      {{ startCase(__(activity.type)) }}
                    </span>
                    <span
                      v-if="activity.data?.old_value"
                      class="max-w-xs font-medium text-ink-gray-8"
                    >
                      <div
                        class="flex items-center gap-1"
                        v-if="activity.options == 'User'"
                      >
                        <UserAvatar :user="activity.data.old_value" size="xs" />
                        {{ getUser(activity.data.old_value).full_name }}
                      </div>
                      <div class="truncate" v-else>
                        {{ activity.data.old_value }}
                      </div>
                    </span>
                    <span v-if="activity.to">{{ __('to') }}</span>
                    <span
                      v-if="activity.data?.value"
                      class="max-w-xs font-medium text-ink-gray-8"
                    >
                      <div
                        class="flex items-center gap-1"
                        v-if="activity.options == 'User'"
                      >
                        <UserAvatar :user="activity.data.value" size="xs" />
                        {{ getUser(activity.data.value).full_name }}
                      </div>
                      <div class="truncate" v-else>
                        {{ activity.data.value }}
                      </div>
                    </span>
                  </div>

                  <div class="ml-auto whitespace-nowrap">
                    <Tooltip :text="formatDate(activity.creation)">
                      <div class="text-sm text-ink-gray-5">
                        {{ __(timeAgo(activity.creation)) }}
                      </div>
                    </Tooltip>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div
        v-else-if="title != 'Emails' && title != 'SMS' && title != 'Activity'"
        v-for="(activity, i) in activities"
        class="activity px-3 sm:px-10"
        :class="
          ['Activity', 'Emails'].includes(title)
            ? 'grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4'
            : ''
        "
      >
        <div
          v-if="['Activity', 'Emails'].includes(title)"
          class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
          :class="[i != activities.length - 1 ? 'before:h-full' : 'before:h-4']"
        >
          <div
            class="flex h-7 w-7 items-center justify-center bg-surface-white"
            :class="{
              'mt-2.5': ['communication'].includes(activity.activity_type),
              'bg-surface-white': ['added', 'removed', 'changed'].includes(
                activity.activity_type,
              ),
              'h-8': [
                'comment',
                'communication',
                'incoming_call',
                'outgoing_call',
              ].includes(activity.activity_type),
            }"
          >
            <UserAvatar
              v-if="activity.activity_type == 'communication'"
              :user="activity.data.sender"
              size="md"
            />
            <MissedCallIcon
              v-else-if="
                ['incoming_call', 'outgoing_call'].includes(
                  activity.activity_type,
                ) && activity.status == 'No Answer'
              "
              class="text-ink-red-4"
            />
            <DeclinedCallIcon
              v-else-if="
                ['incoming_call', 'outgoing_call'].includes(
                  activity.activity_type,
                ) && activity.status == 'Busy'
              "
            />
            <component
              v-else
              :is="activity.icon"
              :class="
                ['added', 'removed', 'changed'].includes(activity.activity_type)
                  ? 'text-ink-gray-4'
                  : 'text-ink-gray-8'
              "
            />
          </div>
        </div>
        <div v-if="activity.activity_type == 'communication'" class="pb-5 mt-px">
          <template v-if="activity.data?.communication_medium === 'SMS'">
            <div class="cursor-pointer flex flex-col rounded-md shadow bg-surface-cards px-3 py-1.5 text-base">
              <div class="-mb-0.5 flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 truncate text-ink-gray-9">
                  <span>
                    {{
                      activity.data.sender_full_name === currentUser.full_name
                        ? __('You')
                        : activity.data.sender_full_name || activity.data.sender || __('You')
                    }}
                  </span>
                </div>
                <Tooltip :text="formatDate(activity.communication_date || activity.creation)">
                  <div class="text-sm text-ink-gray-5">
                    {{ __(timeAgo(activity.communication_date || activity.creation)) }}
                  </div>
                </Tooltip>
              </div>
              <div class="border-0 border-t mt-3 mb-1 border-outline-gray-modals" />
              <div class="text-ink-gray-8 whitespace-pre-wrap">{{ activity.data.content }}</div>
            </div>
          </template>
          <EmailArea v-else :activity="activity" :emailBox="emailBox" />
        </div>
        <div
          class="mb-4"
          :id="activity.name"
          v-else-if="activity.activity_type == 'comment'"
        >
          <CommentArea :activity="activity" />
        </div>
        <div
          class="mb-4 flex flex-col gap-2 py-1.5"
          :id="activity.name"
          v-else-if="activity.activity_type == 'attachment_log'"
        >
          <div class="flex items-center justify-stretch gap-2 text-base">
            <div
              class="inline-flex items-center flex-wrap gap-1.5 text-ink-gray-8 font-medium"
            >
              <span class="font-medium">{{ activity.owner_name }}</span>
              <span class="text-ink-gray-5">{{ __(activity.data.type) }}</span>
              <a
                v-if="activity.data.file_url"
                :href="activity.data.file_url"
                target="_blank"
              >
                <span>{{ activity.data.file_name }}</span>
              </a>
              <span v-else>{{ activity.data.file_name }}</span>
              <FeatherIcon
                v-if="activity.data.is_private"
                name="lock"
                class="size-3"
              />
            </div>
            <div class="ml-auto whitespace-nowrap">
              <Tooltip :text="formatDate(activity.creation)">
                <div class="text-sm text-ink-gray-5">
                  {{ __(timeAgo(activity.creation)) }}
                </div>
              </Tooltip>
            </div>
          </div>
        </div>
        <div
          v-else-if="
            activity.activity_type == 'incoming_call' ||
            activity.activity_type == 'outgoing_call'
          "
          class="mb-4"
        >
          <CallArea :activity="activity" />
        </div>
        <div v-else class="mb-4 flex flex-col gap-2 py-1.5">
          <div class="flex items-center justify-stretch gap-2 text-base">
            <div
              v-if="activity.other_versions"
              class="inline-flex flex-wrap gap-1.5 text-ink-gray-8 font-medium"
            >
              <span>{{ activity.show_others ? __('Hide') : __('Show') }}</span>
              <span> +{{ activity.other_versions.length + 1 }} </span>
              <span>{{ __('changes from') }}</span>
              <span>{{ activity.owner_name }}</span>
              <Button
                class="!size-4"
                variant="ghost"
                :icon="SelectIcon"
                @click="activity.show_others = !activity.show_others"
              />
            </div>
            <div
              v-else
              class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5"
            >
              <span class="font-medium text-ink-gray-8">
                {{ activity.owner_name }}
              </span>
              <span v-if="activity.type">{{ __(activity.type) }}</span>
              <span
                v-if="activity.data?.field_label"
                class="max-w-xs truncate font-medium text-ink-gray-8"
              >
                {{ __(activity.data.field_label) }}
              </span>
              <span v-if="activity.value">{{ __(activity.value) }}</span>
              <span
                v-if="activity.data?.old_value"
                class="max-w-xs font-medium text-ink-gray-8"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.old_value" size="xs" />
                  {{ getUser(activity.data.old_value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.old_value }}
                </div>
              </span>
              <span v-if="activity.to">{{ __('to') }}</span>
              <span
                v-if="activity.data?.value"
                class="max-w-xs font-medium text-ink-gray-8"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.value" size="xs" />
                  {{ getUser(activity.data.value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.value }}
                </div>
              </span>
            </div>

            <div class="ml-auto whitespace-nowrap">
              <Tooltip :text="formatDate(activity.creation)">
                <div class="text-sm text-ink-gray-5">
                  {{ __(timeAgo(activity.creation)) }}
                </div>
              </Tooltip>
            </div>
          </div>
          <div
            v-if="activity.other_versions && activity.show_others"
            class="flex flex-col gap-0.5"
          >
            <div
              v-for="activity in [activity, ...activity.other_versions]"
              class="flex items-start justify-stretch gap-2 py-1.5 text-base"
            >
              <div class="inline-flex flex-wrap gap-1 text-ink-gray-5">
                <span
                  v-if="activity.data?.field_label"
                  class="max-w-xs truncate text-ink-gray-5"
                >
                  {{ __(activity.data.field_label) }}
                </span>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-1 h-4 w-4 text-ink-gray-5"
                />
                <span v-if="activity.type">
                  {{ startCase(__(activity.type)) }}
                </span>
                <span
                  v-if="activity.data?.old_value"
                  class="max-w-xs font-medium text-ink-gray-8"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.old_value" size="xs" />
                    {{ getUser(activity.data.old_value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.old_value }}
                  </div>
                </span>
                <span v-if="activity.to">{{ __('to') }}</span>
                <span
                  v-if="activity.data?.value"
                  class="max-w-xs font-medium text-ink-gray-8"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.value" size="xs" />
                    {{ getUser(activity.data.value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.value }}
                  </div>
                </span>
              </div>

              <div class="ml-auto whitespace-nowrap">
                <Tooltip :text="formatDate(activity.creation)">
                  <div class="text-sm text-ink-gray-5">
                    {{ __(timeAgo(activity.creation)) }}
                  </div>
                </Tooltip>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- Threaded emails block -->
      <div v-else class="px-3 sm:px-10">
        <div v-for="thread in emailThreads" :key="thread.subject" class="activity">
          <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4">
            <div class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-outline-gray-modals before:h-full">
              <div class="z-10 flex h-8 w-7 items-center justify-center bg-surface-white">
                <UserAvatar :user="thread.items[thread.items.length - 1].data.sender" size="md" />
              </div>
            </div>
            <div class="pb-5 mt-px w-full">
              <EmailThread :thread="thread" :emailBox="emailBox" />
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="title == 'Data'" class="h-full flex flex-col px-3 sm:px-10">
      <DataFields
        :doctype="doctype"
        :docname="docname"
        @beforeSave="(data) => emit('beforeSave', data)"
        @afterSave="(data) => emit('afterSave', data)"
      />
    </div>
    <div
      v-else
      class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <component :is="emptyTextIcon" class="h-10 w-10" />
      <span>{{ __(emptyText) }}</span>
      <MultiActionButton v-if="title == 'Calls'" :options="callActions" />
      <Button
        v-else-if="title == 'Notes'"
        :label="__('Create Note')"
        @click="modalRef.showNote()"
      />
      <Button
        v-else-if="title == 'Emails'"
        :label="__('New Email')"
        @click="emailBox.show = true"
      />
      <Button
        v-else-if="title == 'Comments'"
        :label="__('New Comment')"
        @click="emailBox.showComment = true"
      />
      <Button
        v-else-if="title == 'Tasks'"
        :label="__('Create Task')"
        @click="modalRef.showTask()"
      />
      <Button
        v-else-if="title == 'Attachments'"
        :label="__('Upload Attachment')"
        @click="showFilesUploader = true"
      />
    </div>
  </FadedScrollableDiv>
  <div>
    <CommunicationArea
      ref="emailBox"
      v-if="['Emails', 'Comments', 'Activity'].includes(title)"
      v-model="doc"
      v-model:reload="reload_email"
      :doctype="doctype"
      @scroll="scroll"
    />
    <WhatsAppBox
      ref="whatsappBox"
      v-if="title == 'WhatsApp'"
      v-model="doc"
      v-model:reply="replyMessage"
      v-model:whatsapp="whatsappMessages"
      :doctype="doctype"
      @scroll="scroll"
    />
    <SmsBox
      ref="smsBox"
      v-if="title == 'SMS'"
      v-model="doc"
      :doctype="doctype"
  @sent="() => { all_activities.reload(); scroll() }"
    />
  </div>
  <WhatsappTemplateSelectorModal
    v-if="whatsappEnabled"
    v-model="showWhatsappTemplates"
    :doctype="doctype"
    @send="(t) => sendTemplate(t)"
  />
  <AllModals
    ref="modalRef"
    v-model="all_activities"
    :doctype="doctype"
    :doc="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    :doctype="doctype"
    :docname="docname"
    @after="
      () => {
        all_activities.reload()
        changeTabTo('attachments')
      }
    "
  />
</template>
<script setup>
import ActivityHeader from '@/components/Activities/ActivityHeader.vue'
import EmailArea from '@/components/Activities/EmailArea.vue'
import EmailThread from '@/components/Activities/EmailThread.vue'
import SmsThread from '@/components/Activities/SmsThread.vue'
import CommentArea from '@/components/Activities/CommentArea.vue'
import CallArea from '@/components/Activities/CallArea.vue'
import NoteArea from '@/components/Activities/NoteArea.vue'
import TaskArea from '@/components/Activities/TaskArea.vue'
import AttachmentArea from '@/components/Activities/AttachmentArea.vue'
import DataFields from '@/components/Activities/DataFields.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import WhatsAppArea from '@/components/Activities/WhatsAppArea.vue'
import WhatsAppBox from '@/components/Activities/WhatsAppBox.vue'
import SmsBox from '@/components/Activities/SmsBox.vue'
import SmsIcon from '@/components/Icons/SmsIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import MultiActionButton from '@/components/MultiActionButton.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import SelectIcon from '@/components/Icons/SelectIcon.vue'
import MissedCallIcon from '@/components/Icons/MissedCallIcon.vue'
import DeclinedCallIcon from '@/components/Icons/DeclinedCallIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import CommunicationArea from '@/components/CommunicationArea.vue'
import WhatsappTemplateSelectorModal from '@/components/Modals/WhatsappTemplateSelectorModal.vue'
import AllModals from '@/components/Activities/AllModals.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import { timeAgo, formatDate, startCase } from '@/utils'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { capture } from '@/telemetry'
import { Button, Tooltip, createResource } from 'frappe-ui'
import { useElementVisibility } from '@vueuse/core'
import {
  ref,
  computed,
  h,
  markRaw,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRoute } from 'vue-router'

const { makeCall, $socket } = globalStore()
const { getUser } = usersStore()
const currentUser = computed(() => getUser() || {})

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  docname: {
    type: String,
    default: '',
  },
  tabs: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['beforeSave', 'afterSave'])

const route = useRoute()

const reload = defineModel('reload')
const tabIndex = defineModel('tabIndex')

const { document: _document } = useDocument(props.doctype, props.docname)

const doc = computed(() => _document.doc || {})

const reload_email = ref(false)
const modalRef = ref(null)
const showFilesUploader = ref(false)

const title = computed(() => props.tabs?.[tabIndex.value]?.name || 'Activity')

const changeTabTo = (tabName) => {
  const tabNames = props.tabs?.map((tab) => tab.name?.toLowerCase())
  const index = tabNames?.indexOf(tabName)
  if (index == -1) return
  tabIndex.value = index
}

const all_activities = createResource({
  url: 'crm.api.activities.get_activities',
  params: { name: props.docname },
  cache: ['activity', props.docname],
  auto: true,
  transform: ([versions, calls, notes, tasks, attachments]) => {
    return { versions, calls, notes, tasks, attachments }
  },
  onSuccess: () => nextTick(() => scroll()),
})

const showWhatsappTemplates = ref(false)

const whatsappMessages = createResource({
  url: 'crm.api.whatsapp.get_whatsapp_messages',
  cache: ['whatsapp_messages', props.docname],
  params: {
    reference_doctype: props.doctype,
    reference_name: props.docname,
  },
  auto: whatsappEnabled.value,
  transform: (data) => sortByCreation(data),
  onSuccess: () => nextTick(() => scroll()),
})

onBeforeUnmount(() => {
  $socket.off('whatsapp_message')
  $socket.off('sms_message')
})

onMounted(() => {
  $socket.on('whatsapp_message', (data) => {
    if (
      data.reference_doctype === props.doctype &&
      data.reference_name === props.docname
    ) {
      whatsappMessages.reload()
    }
  })

  $socket.on('sms_message', (data) => {
    if (
      data.reference_doctype === props.doctype &&
      data.reference_name === doc.value.data.name
    ) {
  all_activities.reload()
    }
  })

  nextTick(() => {
    const hash = route.hash.slice(1) || null
    let tabNames = props.tabs?.map((tab) => tab.name)
    if (!tabNames?.includes(hash)) {
      scroll(hash)
    }
  })
})

function sendTemplate(template) {
  showWhatsappTemplates.value = false
  capture('send_whatsapp_template', { doctype: props.doctype })
  createResource({
    url: 'crm.api.whatsapp.send_whatsapp_template',
    params: {
      reference_doctype: props.doctype,
      reference_name: props.docname,
      to: doc.value.mobile_no,
      template,
    },
    auto: true,
  })
}

const replyMessage = ref({})

function get_activities() {
  if (!all_activities.data?.versions) return []
  if (!all_activities.data?.calls.length)
    return all_activities.data.versions || []
  return [...all_activities.data.versions, ...all_activities.data.calls]
}

const activities = computed(() => {
  let _activities = []
  if (title.value == 'Activity') {
    // Start with base activities (versions + calls)
    _activities = get_activities().filter((a) => {
      if (a.activity_type !== 'communication') return true
      const medium = a.data?.communication_medium || 'Email'
      // Exclude Email & SMS communications from raw list; they will appear threaded
      return !['Email', 'SMS'].includes(medium)
    })
  } else if (title.value == 'Emails') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) =>
        activity.activity_type === 'communication' &&
        (!activity.data?.communication_medium ||
          activity.data?.communication_medium === 'Email'),
    )
  } else if (title.value == 'SMS') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) =>
        activity.activity_type === 'communication' &&
        activity.data?.communication_medium === 'SMS',
    )
  } else if (title.value == 'Comments') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) => activity.activity_type === 'comment',
    )
  } else if (title.value == 'Calls') {
    if (!all_activities.data?.calls) return []
    return sortByCreation(all_activities.data.calls)
  } else if (title.value == 'Tasks') {
    if (!all_activities.data?.tasks) return []
    return sortByModified(all_activities.data.tasks)
  } else if (title.value == 'Notes') {
    if (!all_activities.data?.notes) return []
    return sortByModified(all_activities.data.notes)
  } else if (title.value == 'Attachments') {
    if (!all_activities.data?.attachments) return []
    return sortByModified(all_activities.data.attachments)
  }

  _activities.forEach((activity) => {
    activity.icon = timelineIcon(activity.activity_type, activity.is_lead)

    if (
      activity.activity_type == 'incoming_call' ||
      activity.activity_type == 'outgoing_call' ||
      activity.activity_type == 'communication'
    )
      return

    update_activities_details(activity)

    if (activity.other_versions) {
      activity.show_others = false
      activity.other_versions.forEach((other_version) => {
        update_activities_details(other_version)
      })
    }
  })
  return sortByCreation(_activities)
})

// Group emails by normalized subject for threaded view
const emailThreads = computed(() => {
  // For Emails tab: activities already filtered to email communications
  // For Activity tab: need to build from all versions since we filtered out in activities list
  if (!['Emails', 'Activity'].includes(title.value)) return []
  let comms
  if (title.value === 'Emails') {
    comms = activities.value
  } else {
    // Activity tab: build from versions list directly
    comms = (all_activities.data?.versions || []).filter(
      (a) =>
        a.activity_type === 'communication' &&
        (!a.data?.communication_medium || a.data?.communication_medium === 'Email'),
    )
  }
  const normalize = (s = '') =>
    s
      .replace(/^\s*/g, '')
      .replace(/^(re|fw|fwd):\s*/gi, '')
      .trim()
  const map = new Map()
  for (const a of comms) {
    const subj = normalize(a.data?.subject || a.subject || '') || '(no subject)'
    if (!map.has(subj)) map.set(subj, [])
    map.get(subj).push(a)
  }
  const threads = []
  for (const [subject, items] of map.entries()) {
    items.sort((x, y) => new Date(x.creation) - new Date(y.creation))
    threads.push({ subject, items })
  }
  threads.sort(
    (A, B) =>
      new Date(A.items[A.items.length - 1].creation) -
      new Date(B.items[B.items.length - 1].creation),
  )
  return threads
})
// Group SMS messages by date (YYYY-MM-DD portion of communication_date/creation)
const smsThreads = computed(() => {
  if (!['SMS', 'Activity'].includes(title.value)) return []
  let comms
  if (title.value === 'SMS') {
    comms = activities.value
  } else {
    comms = (all_activities.data?.versions || []).filter(
      (a) => a.activity_type === 'communication' && a.data?.communication_medium === 'SMS',
    )
  }
  const map = new Map()
  for (const a of comms) {
    const dt = a.communication_date || a.creation
    if (!dt) continue
    const dateKey = dt.slice(0, 10)
    if (!map.has(dateKey)) map.set(dateKey, [])
    map.get(dateKey).push(a)
  }
  const threads = []
  for (const [date, items] of map.entries()) {
    items.sort((x, y) => new Date(x.creation) - new Date(y.creation))
    threads.push({ date, items })
  }
  threads.sort((A, B) => new Date(A.items[A.items.length - 1].creation) - new Date(B.items[B.items.length - 1].creation))
  return threads
})
// Unified timeline for Activity tab: interleave latest email thread, sms thread, notes, and other activities by their last/own creation timestamp
const activityTimeline = computed(() => {
  if (title.value !== 'Activity') return []
  // Build thread items with timestamp equal to last message creation
  const emailThreadItems = emailThreads.value.map((t) => ({
    kind: 'email_thread',
    thread: t,
    ts: new Date(t.items[t.items.length - 1].creation).getTime(),
    key: 'et-' + t.subject,
  }))
  const smsThreadItems = smsThreads.value.map((t) => ({
    kind: 'sms_thread',
    thread: t,
    ts: new Date(t.items[t.items.length - 1].creation).getTime(),
    key: 'st-' + t.date,
  }))
  const noteItems = (all_activities.data?.notes || []).map((n) => ({
    kind: 'note',
    note: n,
    ts: new Date(n.modified || n.creation).getTime(),
    key: 'nt-' + n.name,
  }))
  // Remaining activities already exclude email/sms communications
  const otherItems = activities.value.map((a) => ({
    kind: 'activity',
    activity: a,
    ts: new Date(a.creation).getTime(),
    key: 'ac-' + a.name,
  }))
  const merged = [...emailThreadItems, ...smsThreadItems, ...noteItems, ...otherItems]
  // Sort ascending (oldest at top) to preserve existing time ordering pattern
  merged.sort((a, b) => a.ts - b.ts)
  return merged
})

function sortByCreation(list) {
  return list.sort((a, b) => new Date(a.creation) - new Date(b.creation))
}
function sortByModified(list) {
  return list.sort((b, a) => new Date(a.modified) - new Date(b.modified))
}

function update_activities_details(activity) {
  activity.owner_name = getUser(activity.owner).full_name
  activity.type = ''
  activity.value = ''
  activity.to = ''

  if (activity.activity_type == 'creation') {
    activity.type = activity.data
  } else if (activity.activity_type == 'added') {
    activity.type = 'added'
    activity.value = 'as'
  } else if (activity.activity_type == 'removed') {
    activity.type = 'removed'
    activity.value = 'value'
  } else if (activity.activity_type == 'changed') {
    activity.type = 'changed'
    activity.value = 'from'
    activity.to = 'to'
  }
}

const emptyText = computed(() => {
  let text = 'No Activities'
  if (title.value == 'Emails') {
    text = 'No Email Communications'
  } else if (title.value == 'Comments') {
    text = 'No Comments'
  } else if (title.value == 'Data') {
    text = 'No Data'
  } else if (title.value == 'Calls') {
    text = 'No Call Logs'
  } else if (title.value == 'Notes') {
    text = 'No Notes'
  } else if (title.value == 'Tasks') {
    text = 'No Tasks'
  } else if (title.value == 'Attachments') {
    text = 'No Attachments'
  } else if (title.value == 'WhatsApp') {
    text = 'No WhatsApp Messages'
  } else if (title.value == 'SMS') {
    text = 'No SMS Messages'
  }
  return text
})

const emptyTextIcon = computed(() => {
  let icon = ActivityIcon
  if (title.value == 'Emails') {
    icon = Email2Icon
  } else if (title.value == 'Comments') {
    icon = CommentIcon
  } else if (title.value == 'Data') {
    icon = DetailsIcon
  } else if (title.value == 'Calls') {
    icon = PhoneIcon
  } else if (title.value == 'Notes') {
    icon = NoteIcon
  } else if (title.value == 'Tasks') {
    icon = TaskIcon
  } else if (title.value == 'Attachments') {
    icon = AttachmentIcon
  } else if (title.value == 'WhatsApp') {
    icon = WhatsAppIcon
  } else if (title.value == 'SMS') {
    icon = SmsIcon
  }
  return h(icon, { class: 'text-ink-gray-4' })
})

function timelineIcon(activity_type, is_lead) {
  let icon
  switch (activity_type) {
    case 'creation':
      icon = is_lead ? LeadsIcon : DealsIcon
      break
    case 'deal':
      icon = DealsIcon
      break
    case 'comment':
      icon = CommentIcon
      break
    case 'incoming_call':
      icon = InboundCallIcon
      break
    case 'outgoing_call':
      icon = OutboundCallIcon
      break
    case 'attachment_log':
      icon = AttachmentIcon
      break
    default:
      icon = DotIcon
  }

  return markRaw(icon)
}

const emailBox = ref(null)
const whatsappBox = ref(null)
const smsBox = ref(null)

watch([reload, reload_email], ([reload_value, reload_email_value]) => {
  if (reload_value || reload_email_value) {
    all_activities.reload()
    _document.reload()
    reload.value = false
    reload_email.value = false
  }
})

function scroll(hash) {
  if (['tasks', 'notes'].includes(route.hash?.slice(1))) return
  setTimeout(() => {
    let el
    if (!hash) {
      let e = document.getElementsByClassName('activity')
      el = e[e.length - 1]
    } else {
      el = document.getElementById(hash)
    }
    if (el && !useElementVisibility(el).value) {
      el.scrollIntoView({ behavior: 'smooth' })
      el.focus()
    }
  }, 500)
}

const callActions = computed(() => {
  let actions = [
    {
      label: __('Log a Call'),
      onClick: () => modalRef.value.createCallLog(),
    },
    {
      label: __('Make a Call'),
      onClick: () => makeCall(doc.value.mobile_no),
      condition: () => callEnabled.value,
    },
  ]

  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})

defineExpose({ emailBox, all_activities, changeTabTo })
</script>
